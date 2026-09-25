import io
import logging
import os
import sys
import time
from datetime import datetime, timezone

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from confluent_kafka import Consumer, KafkaError, TopicPartition

KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "kafka:9092")
KAFKA_GROUP = os.environ.get("KAFKA_CONSUMER_GROUP", "datalake-writer")
TOPIC_EONET = os.environ.get("KAFKA_TOPIC_EONET", "eonet.events")
TOPIC_USGS = os.environ.get("KAFKA_TOPIC_USGS", "usgs.earthquakes")

S3_ENDPOINT = os.environ.get("S3_ENDPOINT", "http://minio:4566")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "minio")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY", "minio12345")
S3_BUCKET = os.environ.get("S3_BUCKET_RAW", "raw")
S3_REGION = os.environ.get("S3_REGION", "us-east-1")

BATCH_MAX_MESSAGES = int(os.environ.get("BATCH_MAX_MESSAGES", "200"))
BATCH_MAX_SECONDS = int(os.environ.get("BATCH_MAX_SECONDS", "30"))

TOPIC_TO_PREFIX = {
    TOPIC_EONET: "eonet",
    TOPIC_USGS: "usgs",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("datalake-writer")


def build_s3(max_attempts=30):
    for attempt in range(1, max_attempts + 1):
        try:
            client = boto3.client(
                "s3",
                endpoint_url=S3_ENDPOINT,
                aws_access_key_id=S3_ACCESS_KEY,
                aws_secret_access_key=S3_SECRET_KEY,
                region_name=S3_REGION,
                config=Config(signature_version="s3v4"),
            )
            client.list_buckets()
            return client
        except Exception as error:
            logger.warning("MinIO indisponible (tentative %s/%s) : %s", attempt, max_attempts, error)
            time.sleep(2)
    raise RuntimeError("Impossible de se connecter a MinIO")


def ensure_bucket(client, bucket):
    try:
        client.head_bucket(Bucket=bucket)
    except ClientError:
        client.create_bucket(Bucket=bucket)
        logger.info("Bucket cree : %s", bucket)


def build_consumer(max_attempts=30):
    for attempt in range(1, max_attempts + 1):
        try:
            consumer = Consumer(
                {
                    "bootstrap.servers": KAFKA_BOOTSTRAP,
                    "group.id": KAFKA_GROUP,
                    "auto.offset.reset": "earliest",
                    "enable.auto.commit": False,
                }
            )
            consumer.list_topics(timeout=5)
            consumer.subscribe([TOPIC_EONET, TOPIC_USGS])
            return consumer
        except Exception as error:
            logger.warning("Kafka indisponible (tentative %s/%s) : %s", attempt, max_attempts, error)
            time.sleep(2)
    raise RuntimeError("Impossible de se connecter au broker Kafka")


def object_key(source_prefix, moment):
    return (
        f"{source_prefix}/"
        f"year={moment:%Y}/month={moment:%m}/day={moment:%d}/hour={moment:%H}/"
        f"{source_prefix}-{moment:%Y%m%dT%H%M%SZ}-{int(moment.timestamp() * 1000)}.jsonl"
    )


def flush_batch(s3_client, consumer, batch, offsets):
    if not batch:
        return
    now = datetime.now(timezone.utc)
    for topic, messages in batch.items():
        if not messages:
            continue
        prefix = TOPIC_TO_PREFIX.get(topic, topic.replace(".", "_"))
        key = object_key(prefix, now)
        body = ("\n".join(messages) + "\n").encode("utf-8")
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=io.BytesIO(body),
            ContentType="application/x-ndjson",
        )
        logger.info("Ecrit %s objets sur s3://%s/%s", len(messages), S3_BUCKET, key)
    if offsets:
        consumer.commit(offsets=list(offsets.values()), asynchronous=False)


def main():
    s3_client = build_s3()
    ensure_bucket(s3_client, S3_BUCKET)
    consumer = build_consumer()

    batch = {TOPIC_EONET: [], TOPIC_USGS: []}
    offsets = {}
    batch_size = 0
    batch_started_at = time.monotonic()

    try:
        while True:
            message = consumer.poll(timeout=1.0)
            elapsed = time.monotonic() - batch_started_at
            if message is None:
                if batch_size > 0 and elapsed >= BATCH_MAX_SECONDS:
                    flush_batch(s3_client, consumer, batch, offsets)
                    batch = {TOPIC_EONET: [], TOPIC_USGS: []}
                    offsets = {}
                    batch_size = 0
                    batch_started_at = time.monotonic()
                continue
            if message.error():
                if message.error().code() == KafkaError._PARTITION_EOF:
                    continue
                logger.error("Erreur consumer : %s", message.error())
                continue
            topic = message.topic()
            batch.setdefault(topic, []).append(message.value().decode("utf-8"))
            offsets[(topic, message.partition())] = TopicPartition(
                topic, message.partition(), message.offset() + 1
            )
            batch_size += 1
            if batch_size >= BATCH_MAX_MESSAGES or elapsed >= BATCH_MAX_SECONDS:
                flush_batch(s3_client, consumer, batch, offsets)
                batch = {TOPIC_EONET: [], TOPIC_USGS: []}
                offsets = {}
                batch_size = 0
                batch_started_at = time.monotonic()
    except KeyboardInterrupt:
        logger.info("Arret demande")
    finally:
        if batch_size > 0:
            flush_batch(s3_client, consumer, batch, offsets)
        consumer.close()


if __name__ == "__main__":
    main()
