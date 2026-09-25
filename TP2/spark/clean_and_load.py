import logging
import os
import sys

import psycopg
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    ArrayType,
    BooleanType,
    DoubleType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
)

POSTGRES_HOST = os.environ["POSTGRES_HOST"]
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
POSTGRES_DB = os.environ["POSTGRES_DB"]
POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]

S3_BUCKET = os.environ.get("S3_BUCKET_RAW", "raw")
AGGREGATION_MAX_KM = float(os.environ.get("AGGREGATION_MAX_KM", "500"))
AGGREGATION_MAX_HOURS = float(os.environ.get("AGGREGATION_MAX_HOURS", "168"))

JDBC_URL = (
    f"jdbc:postgresql://{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    "?stringtype=unspecified"
)
JDBC_PROPERTIES = {
    "user": POSTGRES_USER,
    "password": POSTGRES_PASSWORD,
    "driver": "org.postgresql.Driver",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("spark-job")


EONET_SCHEMA = StructType(
    [
        StructField("id", StringType()),
        StructField("title", StringType()),
        StructField("description", StringType()),
        StructField("link", StringType()),
        StructField("closed", StringType()),
        StructField(
            "categories",
            ArrayType(
                StructType(
                    [
                        StructField("id", StringType()),
                        StructField("title", StringType()),
                    ]
                )
            ),
        ),
        StructField(
            "sources",
            ArrayType(
                StructType(
                    [
                        StructField("id", StringType()),
                        StructField("url", StringType()),
                    ]
                )
            ),
        ),
        StructField(
            "geometry",
            ArrayType(
                StructType(
                    [
                        StructField("date", StringType()),
                        StructField("type", StringType()),
                        StructField("coordinates", StringType()),
                    ]
                )
            ),
        ),
    ]
)

USGS_SCHEMA = StructType(
    [
        StructField("id", StringType()),
        StructField(
            "properties",
            StructType(
                [
                    StructField("mag", DoubleType()),
                    StructField("magType", StringType()),
                    StructField("place", StringType()),
                    StructField("time", LongType()),
                    StructField("tsunami", IntegerType()),
                    StructField("sig", IntegerType()),
                    StructField("url", StringType()),
                ]
            ),
        ),
        StructField(
            "geometry",
            StructType(
                [
                    StructField("type", StringType()),
                    StructField("coordinates", ArrayType(DoubleType())),
                ]
            ),
        ),
    ]
)


def truncate_all():
    with psycopg.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        autocommit=True,
    ) as connection:
        connection.execute(
            "TRUNCATE event_earthquake, event_category, event_source, "
            "geometry, earthquake, event, category, source "
            "RESTART IDENTITY CASCADE"
        )
    logger.info("Tables Postgres tronquees")


def write_jdbc(dataframe, table):
    (
        dataframe.write.mode("append")
        .option("driver", JDBC_PROPERTIES["driver"])
        .jdbc(
            url=JDBC_URL,
            table=table,
            properties=JDBC_PROPERTIES,
        )
    )
    logger.info("Ecrit dans %s", table)


def process_eonet(spark):
    df = (
        spark.read.schema(EONET_SCHEMA)
        .option("recursiveFileLookup", "true")
        .json(f"s3a://{S3_BUCKET}/eonet/")
        .filter(F.col("id").isNotNull() & F.col("title").isNotNull() & F.col("link").isNotNull())
        .withColumn("title", F.trim(F.col("title")))
        .filter(F.length(F.col("title")) > 0)
        .filter(F.col("link").rlike("^https?://"))
        .withColumn("closed_ts", F.to_timestamp("closed"))
        .dropDuplicates(["id"])
        .cache()
    )
    total = df.count()
    logger.info("Events EONET candidats : %s", total)

    events_df = df.select(
        F.col("id"),
        F.col("title"),
        F.col("description"),
        F.col("link"),
        F.col("closed_ts").alias("closed"),
    )
    write_jdbc(events_df, "event")

    categories_df = (
        df.select(F.explode_outer("categories").alias("c"), "id")
        .filter(F.col("c").isNotNull())
        .select(
            F.col("c.id").alias("id"),
            F.coalesce(F.col("c.title"), F.col("c.id")).alias("title"),
        )
        .dropDuplicates(["id"])
    )
    write_jdbc(categories_df, "category")

    sources_df = (
        df.select(F.explode_outer("sources").alias("s"))
        .filter(F.col("s").isNotNull() & F.col("s.url").isNotNull())
        .filter(F.col("s.url").rlike("^https?://"))
        .select(
            F.col("s.id").alias("id"),
            F.col("s.url").alias("url"),
        )
        .dropDuplicates(["id"])
    )
    write_jdbc(sources_df, "source")

    event_category_df = (
        df.select(F.col("id").alias("event_id"), F.explode_outer("categories").alias("c"))
        .filter(F.col("c").isNotNull())
        .select("event_id", F.col("c.id").alias("category_id"))
        .dropDuplicates()
    )
    write_jdbc(event_category_df, "event_category")

    event_source_df = (
        df.select(F.col("id").alias("event_id"), F.explode_outer("sources").alias("s"))
        .filter(F.col("s").isNotNull() & F.col("s.url").isNotNull())
        .filter(F.col("s.url").rlike("^https?://"))
        .select("event_id", F.col("s.id").alias("source_id"))
        .dropDuplicates()
    )
    write_jdbc(event_source_df, "event_source")

    geometry_df = (
        df.select(F.col("id").alias("event_id"), F.explode_outer("geometry").alias("g"))
        .filter(F.col("g").isNotNull())
        .filter(F.col("g.type").isin("Point", "Polygon"))
        .filter(F.col("g.date").isNotNull() & F.col("g.coordinates").isNotNull())
        .select(
            "event_id",
            F.to_timestamp(F.col("g.date")).alias("date"),
            F.col("g.type").alias("type"),
            F.col("g.coordinates").alias("coordinates"),
        )
        .dropDuplicates(["event_id", "date", "coordinates"])
    )
    write_jdbc(geometry_df, "geometry")

    return df


def process_usgs(spark):
    df = (
        spark.read.schema(USGS_SCHEMA)
        .option("recursiveFileLookup", "true")
        .json(f"s3a://{S3_BUCKET}/usgs/")
        .filter(F.col("id").isNotNull())
        .filter(F.col("properties.time").isNotNull())
        .filter(F.size(F.col("geometry.coordinates")) >= 2)
        .withColumn("longitude", F.col("geometry.coordinates")[0])
        .withColumn("latitude", F.col("geometry.coordinates")[1])
        .withColumn(
            "depth_km",
            F.when(F.size(F.col("geometry.coordinates")) >= 3, F.col("geometry.coordinates")[2]).otherwise(None),
        )
        .filter(F.col("longitude").between(-180, 180))
        .filter(F.col("latitude").between(-90, 90))
        .filter(F.col("properties.mag").isNull() | F.col("properties.mag").between(-1, 10))
        .withColumn("time", (F.col("properties.time") / F.lit(1000.0)).cast("timestamp"))
        .withColumn(
            "url",
            F.when(F.col("properties.url").rlike("^https?://"), F.col("properties.url")).otherwise(None),
        )
        .withColumn("tsunami_bool", F.col("properties.tsunami").cast(BooleanType()))
        .dropDuplicates(["id"])
    )

    earthquake_df = df.select(
        F.col("id"),
        F.col("time"),
        F.col("properties.mag").alias("magnitude"),
        F.col("properties.magType").alias("mag_type"),
        F.col("properties.place").alias("place"),
        F.col("longitude"),
        F.col("latitude"),
        F.col("depth_km"),
        F.coalesce(F.col("tsunami_bool"), F.lit(False)).alias("tsunami"),
        F.col("properties.sig").alias("significance"),
        F.col("url"),
    )
    write_jdbc(earthquake_df, "earthquake")

    return earthquake_df.select("id", "time", "longitude", "latitude")


def compute_event_earthquake(eonet_df, earthquake_df):
    from pyspark.sql.functions import from_json

    point_geometry = (
        eonet_df.select(
            F.col("id").alias("event_id"),
            F.explode_outer("geometry").alias("g"),
        )
        .filter(F.col("g.type") == F.lit("Point"))
        .withColumn(
            "coords_array",
            from_json(F.col("g.coordinates"), ArrayType(DoubleType())),
        )
        .filter(F.size("coords_array") >= 2)
        .select(
            "event_id",
            F.to_timestamp(F.col("g.date")).alias("event_time"),
            F.col("coords_array")[0].alias("event_lon"),
            F.col("coords_array")[1].alias("event_lat"),
        )
    )

    joined = point_geometry.join(
        earthquake_df.withColumnRenamed("id", "earthquake_id"),
        F.abs(
            (F.unix_timestamp("event_time") - F.unix_timestamp(F.col("time"))) / F.lit(3600.0)
        ) <= F.lit(AGGREGATION_MAX_HOURS),
    )

    R = 6371.0
    lat1 = F.radians("event_lat")
    lat2 = F.radians("latitude")
    dlat = F.radians(F.col("latitude") - F.col("event_lat"))
    dlon = F.radians(F.col("longitude") - F.col("event_lon"))
    a = F.sin(dlat / 2) ** 2 + F.cos(lat1) * F.cos(lat2) * (F.sin(dlon / 2) ** 2)
    distance_km = R * 2 * F.asin(F.sqrt(a))

    delay_hours = (F.unix_timestamp("time") - F.unix_timestamp("event_time")) / F.lit(3600.0)

    aggregated = (
        joined.withColumn("distance_km", distance_km)
        .withColumn("delay_hours", delay_hours)
        .filter(F.col("distance_km") <= F.lit(AGGREGATION_MAX_KM))
        .select(
            "event_id",
            "earthquake_id",
            F.round("distance_km", 2).alias("distance_km"),
            F.round("delay_hours", 2).alias("delay_hours"),
        )
        .dropDuplicates(["event_id", "earthquake_id"])
    )

    count = aggregated.count()
    logger.info("Rapprochements event_earthquake : %s", count)
    write_jdbc(aggregated, "event_earthquake")


def main():
    spark = (
        SparkSession.builder.appName("tp2-clean-and-load")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    try:
        truncate_all()
        eonet_df = process_eonet(spark)
        earthquake_df = process_usgs(spark)
        compute_event_earthquake(eonet_df, earthquake_df)
        logger.info("Pipeline termine avec succes")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
