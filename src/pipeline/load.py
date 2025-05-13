# import json
# import logging

# from confluent_kafka import Consumer, KafkaError, KafkaException
# from sqlalchemy import (
#     create_engine, Column, String, Float, Boolean, Integer,
#     DateTime, JSON, MetaData, Table
# )
# from sqlalchemy.dialects.postgresql import insert
# from sqlalchemy.orm import sessionmaker
# from pydantic import ValidationError

# from ..configs.config import Config
# from ..models.campground import Campground

# cfg             = Config()
# DATABASE_URL    = cfg.database_url
# KAFKA_BOOTSTRAP = ",".join(cfg.kafka["brokers"])
# ENRICHED_TOPIC  = cfg.kafka["topic_enriched"]
# GROUP_ID        = cfg.kafka["group_load"]

# log_level = getattr(logging, cfg.logging_level.upper(), logging.INFO)
# log_file = "logs/kafka_logs/load.log"
# logging.basicConfig(
#     level=log_level,
#     format="%(asctime)s [%(levelname)s] %(message)s",
#     handlers=[
#         logging.FileHandler(log_file),
#         logging.StreamHandler()
#     ]
# )
# logger = logging.getLogger("load")


# meta = MetaData()
# campgrounds = Table(
#     "campgrounds", meta,
#     Column("id",                      String,   primary_key=True),
#     Column("type",                    String,   nullable=False),
#     Column("links_self",              String,   nullable=False),
#     Column("name",                    String,   nullable=False),
#     Column("latitude",                Float,    nullable=False),
#     Column("longitude",               Float,    nullable=False),
#     Column("region_name",             String,   nullable=False),
#     Column("administrative_area",     String,   nullable=True),
#     Column("nearest_city_name",       String,   nullable=True),
#     Column("accommodation_type_names",JSON,     nullable=False),
#     Column("bookable",                Boolean,  nullable=False),
#     Column("camper_types",            JSON,     nullable=False),
#     Column("operator",                String,   nullable=True),
#     Column("photo_url",               String,   nullable=True),
#     Column("photo_urls",              JSON,     nullable=False),
#     Column("photos_count",            Integer,  nullable=False),
#     Column("rating",                  Float,    nullable=True),
#     Column("reviews_count",           Integer,  nullable=False),
#     Column("slug",                    String,   nullable=True),
#     Column("price_low",               Float,    nullable=True),
#     Column("price_high",              Float,    nullable=True),
#     Column("availability_updated_at", DateTime, nullable=True),
#     Column("address",                 String,   nullable=True),
#     Column("raw",                     JSON,     nullable=False),
# )

# engine = create_engine(DATABASE_URL, future=True)
# meta.create_all(engine)
# Session = sessionmaker(bind=engine)

# class Loader:
#     def __init__(self):
#         self.consumer = Consumer({
#             "bootstrap.servers": KAFKA_BOOTSTRAP,
#             "group.id": GROUP_ID,
#             "auto.offset.reset": "earliest",
#         })
#         self.topic = ENRICHED_TOPIC

#     def run(self):
#         self.consumer.subscribe([self.topic])
#         try:
#             while True:
#                 msg = self.consumer.poll(1.0)
#                 if msg is None:
#                     continue

#                 if msg.error():
#                     if msg.error().code() != KafkaError._PARTITION_EOF:
#                         raise KafkaException(msg.error())
#                     continue

#                 raw_payload = msg.value().decode("utf-8")
#                 try:
#                     cg = Campground.model_validate_json(raw_payload)
#                 except ValidationError as ve:
#                     logger.error("Validation failed: %s", ve)
#                     self.consumer.commit(msg)
#                     continue

#                 json_str = cg.model_dump_json(by_alias=True)
#                 rec = json.loads(json_str)

#                 self._upsert(rec)
#                 self.consumer.commit(msg)

#         except KeyboardInterrupt:
#             logger.info("Loader stopped by user")
#         finally:
#             self.consumer.close()

#     def _upsert(self, rec: dict):
#         stmt = insert(campgrounds).values(
#             id                       = rec["id"],
#             type                     = rec["type"],
#             links_self               = rec["links"]["self"],
#             name                     = rec["name"],
#             latitude                 = rec["latitude"],
#             longitude                = rec["longitude"],
#             region_name              = rec["region-name"],
#             administrative_area      = rec.get("administrative-area"),
#             nearest_city_name        = rec.get("nearest-city-name"),
#             accommodation_type_names = rec["accommodation-type-names"],
#             bookable                 = rec["bookable"],
#             camper_types             = rec["camper-types"],
#             operator                 = rec.get("operator"),
#             photo_url                = rec.get("photo-url"),
#             photo_urls               = rec["photo-urls"],
#             photos_count             = rec["photos-count"],
#             rating                   = rec.get("rating"),
#             reviews_count            = rec["reviews-count"],
#             slug                     = rec.get("slug"),
#             price_low                = rec.get("price-low"),
#             price_high               = rec.get("price-high"),
#             availability_updated_at  = rec.get("availability-updated-at"),
#             address                  = rec.get("address"),
#             raw                      = rec,
#         ).on_conflict_do_update(
#             index_elements=["id"],
#             set_={k: v for k, v in {
#                 **rec,
#                 "links_self":              rec["links"]["self"],
#                 "region_name":             rec["region-name"],
#                 "administrative_area":     rec.get("administrative-area"),
#                 "nearest_city_name":       rec.get("nearest-city-name"),
#                 "accommodation_type_names": rec["accommodation-type-names"],
#                 "photo_urls":              rec["photo-urls"],
#                 "photos_count":            rec["photos-count"],
#                 "reviews_count":           rec["reviews-count"],
#                 "raw":                     rec,
#             }.items() if k in campgrounds.c}
#         )        

#         with Session() as session:
#             session.execute(stmt)
#             session.commit()

#         logger.info("Upserted %s", rec["id"])


# if __name__ == "__main__":
#     Loader().run()


import json
import logging

from confluent_kafka import Consumer, KafkaError, KafkaException
from sqlalchemy import (
    create_engine, Column, String, Float, Boolean, Integer,
    DateTime, JSON, MetaData, Table, text
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker
from pydantic import ValidationError

from ..configs.config import Config
from ..models.campground import Campground

cfg             = Config()
DATABASE_URL    = cfg.database_url
KAFKA_BOOTSTRAP = ",".join(cfg.kafka["brokers"])
ENRICHED_TOPIC  = cfg.kafka["topic_enriched"]
GROUP_ID        = cfg.kafka["group_load"]

log_level = getattr(logging, cfg.logging_level.upper(), logging.INFO)
log_file = "logs/kafka_logs/load.log"
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("load")

engine = create_engine(DATABASE_URL, future=True)
meta = MetaData(schema="casestudy")  # <- Şema burada tanımlandı

# Şema yoksa oluştur (PostgreSQL özelliği)
with engine.connect() as conn:
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS casestudy"))
    conn.commit()

campgrounds = Table(
    "campgrounds", meta,
    Column("id",                      String,   primary_key=True),
    Column("type",                    String,   nullable=False),
    Column("links_self",              String,   nullable=False),
    Column("name",                    String,   nullable=False),
    Column("latitude",                Float,    nullable=False),
    Column("longitude",               Float,    nullable=False),
    Column("region_name",             String,   nullable=False),
    Column("administrative_area",     String,   nullable=True),
    Column("nearest_city_name",       String,   nullable=True),
    Column("accommodation_type_names",JSON,     nullable=False),
    Column("bookable",                Boolean,  nullable=False),
    Column("camper_types",            JSON,     nullable=False),
    Column("operator",                String,   nullable=True),
    Column("photo_url",               String,   nullable=True),
    Column("photo_urls",              JSON,     nullable=False),
    Column("photos_count",            Integer,  nullable=False),
    Column("rating",                  Float,    nullable=True),
    Column("reviews_count",           Integer,  nullable=False),
    Column("slug",                    String,   nullable=True),
    Column("price_low",               Float,    nullable=True),
    Column("price_high",              Float,    nullable=True),
    Column("availability_updated_at", DateTime, nullable=True),
    Column("address",                 String,   nullable=True),
    Column("raw",                     JSON,     nullable=False),
)

meta.create_all(engine)
Session = sessionmaker(bind=engine)

class Loader:
    def __init__(self):
        self.consumer = Consumer({
            "bootstrap.servers": KAFKA_BOOTSTRAP,
            "group.id": GROUP_ID,
            "auto.offset.reset": "earliest",
        })
        self.topic = ENRICHED_TOPIC

    def run(self):
        self.consumer.subscribe([self.topic])
        try:
            while True:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        raise KafkaException(msg.error())
                    continue

                raw_payload = msg.value().decode("utf-8")
                try:
                    cg = Campground.model_validate_json(raw_payload)
                except ValidationError as ve:
                    logger.error("Validation failed: %s", ve)
                    self.consumer.commit(msg)
                    continue

                json_str = cg.model_dump_json(by_alias=True)
                rec = json.loads(json_str)

                self._upsert(rec)
                self.consumer.commit(msg)

        except KeyboardInterrupt:
            logger.info("Loader stopped by user")
        finally:
            self.consumer.close()

    def _upsert(self, rec: dict):
        stmt = insert(campgrounds).values(
            id                       = rec["id"],
            type                     = rec["type"],
            links_self               = rec["links"]["self"],
            name                     = rec["name"],
            latitude                 = rec["latitude"],
            longitude                = rec["longitude"],
            region_name              = rec["region-name"],
            administrative_area      = rec.get("administrative-area"),
            nearest_city_name        = rec.get("nearest-city-name"),
            accommodation_type_names = rec["accommodation-type-names"],
            bookable                 = rec["bookable"],
            camper_types             = rec["camper-types"],
            operator                 = rec.get("operator"),
            photo_url                = rec.get("photo-url"),
            photo_urls               = rec["photo-urls"],
            photos_count             = rec["photos-count"],
            rating                   = rec.get("rating"),
            reviews_count            = rec["reviews-count"],
            slug                     = rec.get("slug"),
            price_low                = rec.get("price-low"),
            price_high               = rec.get("price-high"),
            availability_updated_at  = rec.get("availability-updated-at"),
            address                  = rec.get("address"),
            raw                      = rec,
        ).on_conflict_do_update(
            index_elements=["id"],
            set_={k: v for k, v in {
                **rec,
                "links_self":              rec["links"]["self"],
                "region_name":             rec["region-name"],
                "administrative_area":     rec.get("administrative-area"),
                "nearest_city_name":       rec.get("nearest-city-name"),
                "accommodation_type_names": rec["accommodation-type-names"],
                "photo_urls":              rec["photo-urls"],
                "photos_count":            rec["photos-count"],
                "reviews_count":           rec["reviews-count"],
                "raw":                     rec,
            }.items() if k in campgrounds.c}
        )        

        with Session() as session:
            session.execute(stmt)
            session.commit()

        logger.info("Upserted %s", rec["id"])


if __name__ == "__main__":
    Loader().run()
