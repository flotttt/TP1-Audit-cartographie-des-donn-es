import logging
import os
import sys
import time

import psycopg
import requests
from psycopg.types.json import Jsonb

BASE_URL = os.environ.get("EONET_BASE_URL", "https://eonet.gsfc.nasa.gov/api/v3").rstrip("/")
EVENTS_STATUS = os.environ.get("EONET_STATUS", "open")
EVENTS_DAYS = os.environ.get("EONET_DAYS", "")
EVENTS_LIMIT = os.environ.get("EONET_LIMIT", "")
INTERVAL_SECONDS = int(os.environ.get("WORKER_INTERVAL_SECONDS", "900"))
USER_AGENT = os.environ.get("HTTP_USER_AGENT", "eonet-tp-worker/1.0")

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
logger = logging.getLogger("eonet-worker")


def fetch(path, params=None):
    response = requests.get(
        f"{BASE_URL}/{path}",
        params=params,
        headers={"User-Agent": USER_AGENT},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def connect(max_attempts=30):
    for attempt in range(1, max_attempts + 1):
        try:
            return psycopg.connect(**DB_SETTINGS, autocommit=True)
        except psycopg.OperationalError as error:
            logger.warning("Base indisponible (tentative %s/%s) : %s", attempt, max_attempts, error)
            time.sleep(2)
    raise RuntimeError("Impossible de se connecter à la base")


def upsert_categories(connection, categories):
    with connection.transaction():
        for category in categories:
            connection.execute(
                """
                INSERT INTO category (id, title, description)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO UPDATE
                SET title = EXCLUDED.title, description = EXCLUDED.description
                """,
                (category["id"], category["title"], category.get("description")),
            )


def upsert_sources(connection, sources):
    with connection.transaction():
        for source in sources:
            url = source.get("url") or source.get("source")
            if not url:
                continue
            connection.execute(
                """
                INSERT INTO source (id, url)
                VALUES (%s, %s)
                ON CONFLICT (id) DO UPDATE
                SET url = EXCLUDED.url
                """,
                (source["id"], url),
            )


def upsert_event(connection, event):
    with connection.transaction():
        connection.execute(
            """
            INSERT INTO event (id, title, description, link, closed)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE
            SET title = EXCLUDED.title,
                description = EXCLUDED.description,
                link = EXCLUDED.link,
                closed = EXCLUDED.closed
            """,
            (event["id"], event["title"], event.get("description"), event["link"], event.get("closed")),
        )

        for category in event.get("categories", []):
            connection.execute(
                """
                INSERT INTO category (id, title)
                VALUES (%s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (category["id"], category.get("title") or category["id"]),
            )
            connection.execute(
                """
                INSERT INTO event_category (event_id, category_id)
                VALUES (%s, %s)
                ON CONFLICT (event_id, category_id) DO NOTHING
                """,
                (event["id"], category["id"]),
            )

        for source in event.get("sources", []):
            url = source.get("url")
            if not url:
                continue
            connection.execute(
                """
                INSERT INTO source (id, url)
                VALUES (%s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (source["id"], url),
            )
            connection.execute(
                """
                INSERT INTO event_source (event_id, source_id)
                VALUES (%s, %s)
                ON CONFLICT (event_id, source_id) DO NOTHING
                """,
                (event["id"], source["id"]),
            )

        for geometry in event.get("geometry", []):
            connection.execute(
                """
                INSERT INTO geometry (event_id, date, type, coordinates)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (event_id, date, coordinates) DO NOTHING
                """,
                (
                    event["id"],
                    geometry["date"],
                    geometry["type"],
                    Jsonb(geometry["coordinates"]),
                ),
            )


def events_parameters():
    parameters = {"status": EVENTS_STATUS}
    if EVENTS_DAYS:
        parameters["days"] = EVENTS_DAYS
    if EVENTS_LIMIT:
        parameters["limit"] = EVENTS_LIMIT
    return parameters


def run_once(connection):
    categories = fetch("categories").get("categories", [])
    upsert_categories(connection, categories)
    logger.info("Catégories synchronisées : %s", len(categories))

    sources = fetch("sources").get("sources", [])
    upsert_sources(connection, sources)
    logger.info("Sources synchronisées : %s", len(sources))

    events = fetch("events", events_parameters()).get("events", [])
    failures = 0
    for event in events:
        try:
            upsert_event(connection, event)
        except Exception:
            failures += 1
            logger.exception("Événement ignoré : %s", event.get("id"))
    logger.info("Événements traités : %s, en erreur : %s", len(events), failures)


def main():
    while True:
        try:
            with connect() as connection:
                run_once(connection)
        except Exception:
            logger.exception("Échec de la synchronisation")
            if INTERVAL_SECONDS <= 0:
                sys.exit(1)
        if INTERVAL_SECONDS <= 0:
            break
        logger.info("Prochaine synchronisation dans %s secondes", INTERVAL_SECONDS)
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
