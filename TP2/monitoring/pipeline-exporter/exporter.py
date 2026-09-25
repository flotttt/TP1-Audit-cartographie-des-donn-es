import logging
import os
import sys
import time

import boto3
from botocore.client import Config
import psycopg
from prometheus_client import start_http_server, Gauge

S3_ENDPOINT = os.environ.get("S3_ENDPOINT", "http://minio:4566")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "minio")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY", "minio12345")
S3_BUCKET = os.environ.get("S3_BUCKET_RAW", "raw")
S3_REGION = os.environ.get("S3_REGION", "us-east-1")

POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "db")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
POSTGRES_DB = os.environ["POSTGRES_DB"]
POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]

REFRESH_SECONDS = int(os.environ.get("EXPORTER_REFRESH_SECONDS", "30"))
EXPORTER_PORT = int(os.environ.get("EXPORTER_PORT", "9105"))

SOURCES = {"eonet": "eonet/", "usgs": "usgs/"}
CLEAN_TABLES = {"eonet": "event", "usgs": "earthquake"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("pipeline-exporter")

raw_objects = Gauge("pipeline_raw_objects_total", "Objets bruts dans le Data Lake", ["source"])
raw_lines = Gauge("pipeline_raw_lines_total", "Lignes JSON brutes dans le Data Lake", ["source"])
clean_rows = Gauge("pipeline_clean_rows_total", "Lignes propres en base", ["table"])
scrape_errors = Gauge("pipeline_exporter_errors_total", "Erreurs de refresh de l'exporter")
last_success = Gauge("pipeline_exporter_last_success_timestamp", "Timestamp du dernier refresh reussi")


def build_s3():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        region_name=S3_REGION,
        config=Config(signature_version="s3v4"),
    )


def count_raw(s3_client, prefix):
    objects = 0
    lines = 0
    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix):
        for obj in page.get("Contents", []):
            objects += 1
            body = s3_client.get_object(Bucket=S3_BUCKET, Key=obj["Key"])["Body"].read()
            lines += body.count(b"\n")
    return objects, lines


def count_clean(connection, table):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        return cursor.fetchone()[0]


def refresh():
    s3_client = build_s3()
    for source, prefix in SOURCES.items():
        objects, lines = count_raw(s3_client, prefix)
        raw_objects.labels(source=source).set(objects)
        raw_lines.labels(source=source).set(lines)
        logger.info("Raw %s : %s objets, %s lignes", source, objects, lines)

    with psycopg.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        autocommit=True,
    ) as connection:
        for source, table in CLEAN_TABLES.items():
            count = count_clean(connection, table)
            clean_rows.labels(table=table).set(count)
            logger.info("Clean %s : %s lignes", table, count)


def main():
    start_http_server(EXPORTER_PORT)
    logger.info("Exporter demarre sur le port %s", EXPORTER_PORT)
    while True:
        try:
            refresh()
            last_success.set(time.time())
        except Exception:
            scrape_errors.inc()
            logger.exception("Echec du refresh")
        time.sleep(REFRESH_SECONDS)


if __name__ == "__main__":
    main()
