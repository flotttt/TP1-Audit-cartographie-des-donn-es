import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import psycopg
import requests

BASE_URL = os.environ.get("USGS_BASE_URL", "https://earthquake.usgs.gov/fdsnws/event/1").rstrip("/")
MIN_MAGNITUDE = os.environ.get("USGS_MIN_MAGNITUDE", "4.5")
DAYS = int(os.environ.get("USGS_DAYS", "30"))
LIMIT = os.environ.get("USGS_LIMIT", "500")
INTERVAL_SECONDS = int(os.environ.get("WORKER_INTERVAL_SECONDS", "900"))
USER_AGENT = os.environ.get("HTTP_USER_AGENT", "usgs-tp-worker/1.0")

DB_SETTINGS = {
    "host": os.environ.get("POSTGRES_HOST", "db"),
    "port": int(os.environ.get("POSTGRES_PORT", "5432")),
    "dbname": os.environ.get("POSTGRES_DB", "eonet"),
    "user": os.environ.get("POSTGRES_USER", "eonet"),
    "password": os.environ.get("POSTGRES_PASSWORD", ""),
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("usgs-worker")


def fetch_earthquakes():
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=DAYS)
    params = {
        "format": "geojson",
        "starttime": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "endtime": end.strftime("%Y-%m-%dT%H:%M:%S"),
        "minmagnitude": MIN_MAGNITUDE,
        "orderby": "time",
    }
    if LIMIT:
        params["limit"] = LIMIT
    response = requests.get(
        f"{BASE_URL}/query",
        params=params,
        headers={"User-Agent": USER_AGENT},
        timeout=120,
    )
    response.raise_for_status()
    return response.json().get("features", [])


def connect(max_attempts=30):
    for attempt in range(1, max_attempts + 1):
        try:
            return psycopg.connect(**DB_SETTINGS, autocommit=True)
        except psycopg.OperationalError as error:
            logger.warning("Base indisponible (tentative %s/%s) : %s", attempt, max_attempts, error)
            time.sleep(2)
    raise RuntimeError("Impossible de se connecter a la base")


def upsert_earthquake(connection, feature):
    properties = feature.get("properties", {})
    geometry = feature.get("geometry", {})
    coordinates = geometry.get("coordinates") or []
    if len(coordinates) < 2:
        return
    longitude = coordinates[0]
    latitude = coordinates[1]
    depth = coordinates[2] if len(coordinates) > 2 else None
    epoch_ms = properties.get("time")
    if epoch_ms is None or longitude is None or latitude is None:
        return
    with connection.transaction():
        connection.execute(
            """
            INSERT INTO earthquake (
                id, time, magnitude, mag_type, place,
                longitude, latitude, depth_km, tsunami, significance, url
            )
            VALUES (
                %s, to_timestamp(%s / 1000.0), %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (id) DO UPDATE
            SET time = EXCLUDED.time,
                magnitude = EXCLUDED.magnitude,
                mag_type = EXCLUDED.mag_type,
                place = EXCLUDED.place,
                longitude = EXCLUDED.longitude,
                latitude = EXCLUDED.latitude,
                depth_km = EXCLUDED.depth_km,
                tsunami = EXCLUDED.tsunami,
                significance = EXCLUDED.significance,
                url = EXCLUDED.url
            """,
            (
                feature["id"],
                epoch_ms,
                properties.get("mag"),
                properties.get("magType"),
                properties.get("place"),
                longitude,
                latitude,
                depth,
                bool(properties.get("tsunami")),
                properties.get("sig"),
                properties.get("url"),
            ),
        )


def run_once(connection):
    features = fetch_earthquakes()
    failures = 0
    for feature in features:
        try:
            upsert_earthquake(connection, feature)
        except Exception:
            failures += 1
            logger.exception("Seisme ignore : %s", feature.get("id"))
    logger.info("Seismes traites : %s, en erreur : %s", len(features), failures)


def main():
    while True:
        try:
            with connect() as connection:
                run_once(connection)
        except Exception:
            logger.exception("Echec de la synchronisation")
            if INTERVAL_SECONDS <= 0:
                sys.exit(1)
        if INTERVAL_SECONDS <= 0:
            break
        logger.info("Prochaine synchronisation dans %s secondes", INTERVAL_SECONDS)
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
