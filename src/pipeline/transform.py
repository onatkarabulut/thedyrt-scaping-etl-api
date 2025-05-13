import json
import logging
from typing import List

import numpy as np
import pandas as pd
from confluent_kafka import Consumer, Producer, KafkaError, KafkaException
from pydantic import ValidationError

from ..configs.config import Config
from ..models.campground import Campground

cfg = Config()
kc = cfg.kafka

log_level = getattr(logging, cfg.logging_level.upper(), logging.INFO)
log_file = "logs/kafka_logs/transform.log"
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("transform")

class Transformer:
    def __init__(self):
        self.consumer = Consumer({
            "bootstrap.servers": ",".join(kc["brokers"]),
            "group.id":          kc["group_transform"],
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        })
        self.producer = Producer({
            "bootstrap.servers": ",".join(kc["brokers"]),
            "acks": "all"
        })

        self.raw_topic      = kc["topic_raw"]
        self.enriched_topic = kc["topic_enriched"]
        self.batch_size     = kc.get("batch_size", 100)

    def run(self):
        self.consumer.subscribe([self.raw_topic])
        buffer: List[dict] = []
        try:
            while True:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    if buffer:
                        self._flush(buffer)
                        buffer.clear()
                    continue

                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        raise KafkaException(msg.error())
                    continue

                try:
                    buffer.append(json.loads(msg.value().decode("utf-8")))
                except Exception as e:
                    logger.error("Bad JSON, skipping: %s", e)

                self.consumer.commit(msg)

                if len(buffer) >= self.batch_size:
                    self._flush(buffer)
                    buffer.clear()
        except KeyboardInterrupt:
            logger.info("Interrupted; flushing %d records", len(buffer))
            if buffer:
                self._flush(buffer)
        finally:
            self.consumer.close()
            self.producer.flush()

    def _flush(self, batch: List[dict]):
        df = pd.json_normalize(batch, sep=".")

        df["attributes.price-low"]      = pd.to_numeric(df.get("attributes.price-low", 0),  errors="coerce").fillna(0) / 100
        df["attributes.price-high"]     = pd.to_numeric(df.get("attributes.price-high",0), errors="coerce").fillna(0) / 100
        df["attributes.photos-count"]   = pd.to_numeric(df.get("attributes.photos-count",0), errors="coerce").fillna(0).astype(int)
        df["attributes.reviews-count"]  = pd.to_numeric(df.get("attributes.reviews-count",0), errors="coerce").fillna(0).astype(int)

        enriched = []
        for _, row in df.iterrows():
            links = {"self": row.get("links.self")}
            attrs = {
                col.split("attributes.")[1]: row[col]
                for col in df.columns
                if col.startswith("attributes.")
            }

            payload = {
                "id":    row.get("id"),
                "type":  row.get("type"),
                "links": links,
                **attrs
            }

            try:
                cg = Campground.model_validate(payload)
                rec = json.loads(
                    cg.model_dump_json(by_alias=True)
                )
                enriched.append(rec)
            except ValidationError as e:
                logger.error("Validation failed: %s", e)

        for rec in enriched:
            self.producer.produce(
                self.enriched_topic,
                json.dumps(rec).encode("utf-8"),
                callback=self._delivery_report
            )
            self.producer.poll(0)

        logger.info("Transformed %d → %d", len(batch), len(enriched))

    def _delivery_report(self, err, msg):
        if err:
            logger.error("Delivery failed: %s", err)

if __name__ == "__main__":
    Transformer().run()



