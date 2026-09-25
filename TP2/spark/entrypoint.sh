#!/bin/bash
set -euo pipefail

INTERVAL=${SPARK_INTERVAL_SECONDS:-900}

PACKAGES="org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262,org.postgresql:postgresql:42.7.4"

while true; do
    echo "$(date -u +%FT%TZ) Lancement du job Spark"
    /opt/spark/bin/spark-submit \
        --master "local[*]" \
        --conf spark.jars.ivy=/tmp/.ivy2 \
        --packages "${PACKAGES}" \
        --conf spark.hadoop.fs.s3a.endpoint="${S3_ENDPOINT}" \
        --conf spark.hadoop.fs.s3a.access.key="${S3_ACCESS_KEY}" \
        --conf spark.hadoop.fs.s3a.secret.key="${S3_SECRET_KEY}" \
        --conf spark.hadoop.fs.s3a.path.style.access=true \
        --conf spark.hadoop.fs.s3a.connection.ssl.enabled=false \
        --conf spark.hadoop.fs.s3a.aws.credentials.provider=org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider \
        --conf spark.sql.session.timeZone=UTC \
        /app/clean_and_load.py || echo "Job en erreur"
    echo "$(date -u +%FT%TZ) Fin du job. Pause ${INTERVAL}s."
    sleep "${INTERVAL}"
done
