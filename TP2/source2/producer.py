import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import requests
from confluent_kafka import Producer

BASE_URL = os.environ.get("USGS_BASE_URL", "https://earthquake.usgs.gov/fdsnws/event/1").rstrip("/")
MIN_MAGNITUDE = os.environ.get("USGS_MIN_MAGNITUDE", "4.5")
DAYS = int(os.environ.get("USGS_DAYS", "30"))
LIMIT = os.environ.get("USGS_LIMIT", "500")
INTERVAL_SECONDS = int(os.environ.get("WORKER_INTERVAL_SECONDS", "900"))
USER_AGENT = os.environ.get("HTTP_USER_AGENT", "usgs-tp-producer/1.0")

KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "kafka:9092")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", "usgs.earthquakes")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("usgs-producer")


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


def build_producer(max_attempts=30):
    for attempt in range(1, max_attempts + 1):
        try:
            producer = Producer(
                {
                    "bootstrap.servers": KAFKA_BOOTSTRAP,
                    "client.id": "usgs-producer",
                    "enable.idempotence": True,
                    "acks": "all",
                    "linger.ms": 50,
                }
            )
            producer.list_topics(timeout=5)
            return producer
        except Exception as error:
            logger.warning("Kafka indisponible (tentative %s/%s) : %s", attempt, max_attempts, error)
            time.sleep(2)
    raise RuntimeError("Impossible de se connecter au broker Kafka")


def delivery_report(error, message):
    if error is not None:
        logger.error("Echec envoi Kafka : %s", error)
    else:
        logger.debug("Message livre : %s [%s]", message.topic(), message.partition())


def run_once(producer):
    features = fetch_earthquakes()
    sent = 0
    for feature in features:
        key = feature.get("id")
        if not key:
            continue
        try:
            producer.produce(
                topic=KAFKA_TOPIC,
                key=key.encode("utf-8"),
                value=json.dumps(feature, ensure_ascii=False).encode("utf-8"),
                callback=delivery_report,
            )
            sent += 1
        except BufferError:
            producer.poll(1)
            producer.produce(
                topic=KAFKA_TOPIC,
                key=key.encode("utf-8"),
                value=json.dumps(feature, ensure_ascii=False).encode("utf-8"),
                callback=delivery_report,
            )
            sent += 1
        producer.poll(0)
    producer.flush(30)
    logger.info("Seismes publies sur %s : %s", KAFKA_TOPIC, sent)


def main():
    producer = build_producer()
    while True:
        try:
            run_once(producer)
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
