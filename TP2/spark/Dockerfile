FROM apache/spark:3.5.3

USER root

WORKDIR /app

RUN pip install --no-cache-dir "psycopg[binary]>=3.2,<4"

COPY clean_and_load.py entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

USER spark

ENTRYPOINT ["/app/entrypoint.sh"]
