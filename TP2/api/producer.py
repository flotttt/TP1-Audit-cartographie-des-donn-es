import json
import logging
import os
import sys
import time

import requests
from confluent_kafka import Producer

BASE_URL = os.environ.get("EONET_BASE_URL", "https://eonet.gsfc.nasa.gov/api/v3").rstrip("/")
EVENTS_STATUS = os.environ.get("EONET_STATUS", "open")
EVENTS_DAYS = os.environ.get("EONET_DAYS", "")
EVENTS_LIMIT = os.environ.get("EONET_LIMIT", "")
INTERVAL_SECONDS = int(os.environ.get("WORKER_INTERVAL_SECONDS", "900"))
USER_AGENT = os.environ.get("HTTP_USER_AGENT", "eonet-tp-producer/1.0")

KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "kafka:9092")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", "eonet.events")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("eonet-producer")


def fetch(path, params=None):
    response = requests.get(
        f"{BASE_URL}/{path}",
        params=params,
        headers={"User-Agent": USER_AGENT},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def build_producer(max_attempts=30):
    for attempt in range(1, max_attempts + 1):
        try:
            producer = Producer(
                {
                    "bootstrap.servers": KAFKA_BOOTSTRAP,
                    "client.id": "eonet-producer",
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


def events_parameters():
    parameters = {"status": EVENTS_STATUS}
    if EVENTS_DAYS:
        parameters["days"] = EVENTS_DAYS
    if EVENTS_LIMIT:
        parameters["limit"] = EVENTS_LIMIT
    return parameters


def run_once(producer):
    events = fetch("events", events_parameters()).get("events", [])
    sent = 0
    for event in events:
        try:
            producer.produce(
                topic=KAFKA_TOPIC,
                key=event["id"].encode("utf-8"),
                value=json.dumps(event, ensure_ascii=False).encode("utf-8"),
                callback=delivery_report,
            )
            sent += 1
        except BufferError:
            producer.poll(1)
            producer.produce(
                topic=KAFKA_TOPIC,
                key=event["id"].encode("utf-8"),
                value=json.dumps(event, ensure_ascii=False).encode("utf-8"),
                callback=delivery_report,
            )
            sent += 1
        producer.poll(0)
    producer.flush(30)
    logger.info("Evenements publies sur %s : %s", KAFKA_TOPIC, sent)


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
