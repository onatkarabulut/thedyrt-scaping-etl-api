import argparse
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional

import reverse_geocode
import requests
from confluent_kafka import Producer
from concurrent.futures import ThreadPoolExecutor, as_completed
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.location import Location

from ..configs.config import Config

cfg = Config()
log_level = getattr(logging, cfg.logging_level.upper(), logging.INFO)
logging.basicConfig(level=log_level, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Loader")


class CampgroundExtractor:
    def __init__(self, enable_kafka: bool = True, enable_address: bool = True):
        geocfg = cfg.geocoder

        # Nominatim client
        self.geolocator = Nominatim(user_agent=geocfg["user_agent"])
        self.geocode = RateLimiter(
            self.geolocator.geocode,
            min_delay_seconds=geocfg["rate_limit_seconds"]
        )

        # reverse-geocode: offline first, then online (very slow, low volume)
        self.enable_address = enable_address
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.reverse = RateLimiter(
            self.geolocator.reverse,
            min_delay_seconds=1,
            max_retries=0,
            swallow_exceptions=True
        )

        # API + pagination
        apicfg = cfg.api
        self.base_api = apicfg["search_result_url"]
        self.page_size = apicfg["page_size"]

        # Kafka producer
        self.enable_kafka = enable_kafka
        if self.enable_kafka:
            kafkacfg = cfg.kafka
            brokers = ",".join(kafkacfg["brokers"])
            self.producer = Producer({
                "bootstrap.servers": brokers,
                "client.id": kafkacfg["group_extract"],
                "acks": "all"
            })
            self.topic = kafkacfg["topic_raw"]
            logger.info(f"Kafka ON → topic {self.topic}")

    def _get_bbox(self, state: str) -> str:
        loc = self.geocode(f"{state}, USA", exactly_one=True)
        if not loc:
            raise RuntimeError(f"Cannot geocode {state}")
        sb, nb, wb, eb = loc.raw["boundingbox"]
        return f"{wb},{sb},{eb},{nb}"

    def _send(self, rec: Dict):
        if not self.enable_kafka:
            return
        self.producer.produce(self.topic, json.dumps(rec).encode())
        self.producer.poll(0)

    def _address_str(self, lat: float, lon: float) -> Optional[str]:
        # 1) offline lookup via reverse_geocode
        try:
            info = reverse_geocode.search([(lat, lon)])[0]
            city, state, cc = info["city"], info["state"], info["country_code"]
            return f"{city}, {state}, {cc}"
        except Exception:
            pass

        # 2) fallback to Nominatim reverse (very slow, admitted)
        try:
            loc = self.reverse((lat, lon), exactly_one=True, addressdetails=True)
            if not isinstance(loc, Location):
                return None
            addr = loc.raw.get("address", {})
            return str(addr) if addr else None
        except Exception as e:
            logger.warning(f"Reverse-geocode failed {lat},{lon}: {e}")
            return None

    def _enrich_batch_with_address(self, items: List[dict]) -> List[dict]:
        futures = {}
        for it in items:
            lat = it.get("attributes", {}).get("latitude")
            lon = it.get("attributes", {}).get("longitude")
            if lat is not None and lon is not None:
                futures[self.executor.submit(self._address_str, lat, lon)] = it

        for fut in as_completed(futures):
            rec = futures[fut]
            addr = fut.result()
            if addr:
                rec["attributes"]["address"] = addr
        return items

    def fetch_state(self, state: str):
        bbox = self._get_bbox(state)
        logger.info(f"→ {state} bbox={bbox}")

        params = {
            "filter[search][bbox]": bbox,
            "sort": "recommended",
            "page[number]": 1,
            "page[size]": self.page_size
        }

        while True:
            resp = requests.get(self.base_api, params=params, timeout=10)
            data = resp.json().get("data", [])
            if not data:
                break

            if self.enable_address:
                data = self._enrich_batch_with_address(data)
            else:
                logger.debug("Skipping address enrichment")

            for rec in data:
                self._send(rec)

            logger.info(f"   • page {params['page[number]']} → {len(data)} rec")
            if len(data) < self.page_size:
                break
            params["page[number]"] += 1

        if self.enable_kafka:
            self.producer.flush()
        logger.info(f"[✓] {state} extraction complete")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", help="Single state to extract")
    parser.add_argument("--all", action="store_true", help="Extract all states")
    parser.add_argument("--no-kafka", action="store_true", help="Disable Kafka output")
    parser.add_argument("--no-address", action="store_true", help="Disable reverse-geocoding/address enrichment")
    args = parser.parse_args()

    extractor = CampgroundExtractor(
        enable_kafka=not args.no_kafka,
        enable_address=not args.no_address
    )

    states = [
        "Alabama","Alaska","Arizona","Arkansas","California","Colorado",
        "Connecticut","Delaware","Florida","Georgia","Hawaii","Idaho",
        "Illinois","Indiana","Iowa","Kansas","Kentucky","Louisiana",
        "Maine","Maryland","Massachusetts","Michigan","Minnesota",
        "Mississippi","Missouri","Montana","Nebraska","Nevada",
        "New Hampshire","New Jersey","New Mexico","New York",
        "North Carolina","North Dakota","Ohio","Oklahoma","Oregon",
        "Pennsylvania","Rhode Island","South Carolina","South Dakota",
        "Tennessee","Texas","Utah","Vermont","Virginia","Washington",
        "West Virginia","Wisconsin","Wyoming","District of Columbia"
    ]

    if args.state:
        extractor.fetch_state(args.state)
    elif args.all:
        for st in states:
            try:
                extractor.fetch_state(st)
            except Exception as e:
                logger.error(f"{st} → {e}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()




### NOMINIC REVERSE GEOCODE, THIS IS SLOWER THAN THE OTHER ONE BUT MORE RELIABLE

# import argparse
# import json
# import logging
# from datetime import datetime
# from typing import List, Dict, Optional

# import requests
# from confluent_kafka import Producer
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from geopy.geocoders import Nominatim
# from geopy.extra.rate_limiter import RateLimiter
# from geopy.location import Location

# from ..configs.config import Config

# cfg = Config()
# log_level = getattr(logging, cfg.logging_level.upper(), logging.INFO)
# logging.basicConfig(level=log_level, format="%(asctime)s [%(levelname)s] %(message)s")
# logger = logging.getLogger("Loader")


# class CampgroundExtractor:
#     def __init__(self, enable_kafka: bool = True, enable_address: bool = True):
#         geocfg = cfg.geocoder

#         # Nominatim client
#         self.geolocator = Nominatim(user_agent=geocfg["user_agent"])
#         self.geocode = RateLimiter(
#             self.geolocator.geocode,
#             min_delay_seconds=geocfg["rate_limit_seconds"]
#         )

#         # reverse-geocode only via Nominatim
#         self.enable_address = enable_address
#         self.executor = ThreadPoolExecutor(max_workers=4)
#         self.reverse = RateLimiter(
#             self.geolocator.reverse,
#             min_delay_seconds=geocfg["rate_limit_seconds"],
#             max_retries=2,
#             error_wait_seconds=5,
#             swallow_exceptions=True
#         )

#         # API + pagination
#         apicfg = cfg.api
#         self.base_api = apicfg["search_result_url"]
#         self.page_size = apicfg["page_size"]

#         # Kafka producer
#         self.enable_kafka = enable_kafka
#         if self.enable_kafka:
#             kafkacfg = cfg.kafka
#             brokers = ",".join(kafkacfg["brokers"])
#             self.producer = Producer({
#                 "bootstrap.servers": brokers,
#                 "client.id": kafkacfg["group_extract"],
#                 "acks": "all"
#             })
#             self.topic = kafkacfg["topic_raw"]
#             logger.info(f"Kafka ON → topic {self.topic}")

#     def _get_bbox(self, state: str) -> str:
#         loc = self.geocode(f"{state}, USA", exactly_one=True)
#         if not loc:
#             raise RuntimeError(f"Cannot geocode {state}")
#         sb, nb, wb, eb = loc.raw["boundingbox"]
#         return f"{wb},{sb},{eb},{nb}"

#     def _send(self, rec: Dict):
#         if not self.enable_kafka:
#             return
#         self.producer.produce(self.topic, json.dumps(rec).encode())
#         self.producer.poll(0)

#     def _address_str(self, lat: float, lon: float) -> Optional[str]:
#         """
#         Sadece Nominatim reverse geocoding kullanır.
#         """
#         try:
#             loc: Location = self.reverse((lat, lon), exactly_one=True, addressdetails=True)
#             if not isinstance(loc, Location):
#                 return None
#             addr = loc.raw.get("address", {})
#             # istediğiniz alanları burada seçebilirsiniz
#             parts = []
#             for key in ("road", "suburb", "city", "state", "postcode", "country"):
#                 if key in addr:
#                     parts.append(addr[key])
#             return ", ".join(parts) if parts else None
#         except Exception as e:
#             logger.warning(f"Reverse-geocode failed for {lat},{lon}: {e}")
#             return None

#     def _enrich_batch_with_address(self, items: List[dict]) -> List[dict]:
#         futures = {}
#         for it in items:
#             lat = it.get("attributes", {}).get("latitude")
#             lon = it.get("attributes", {}).get("longitude")
#             if lat is not None and lon is not None:
#                 futures[self.executor.submit(self._address_str, lat, lon)] = it

#         for fut in as_completed(futures):
#             rec = futures[fut]
#             addr_str = fut.result()
#             if addr_str:
#                 rec["attributes"]["address"] = addr_str
#         return items

#     def fetch_state(self, state: str):
#         bbox = self._get_bbox(state)
#         logger.info(f"→ {state} bbox={bbox}")

#         params = {
#             "filter[search][bbox]": bbox,
#             "sort": "recommended",
#             "page[number]": 1,
#             "page[size]": self.page_size
#         }

#         while True:
#             resp = requests.get(self.base_api, params=params, timeout=10)
#             data = resp.json().get("data", [])
#             if not data:
#                 break

#             if self.enable_address:
#                 data = self._enrich_batch_with_address(data)
#             else:
#                 logger.debug("Skipping address enrichment")

#             for rec in data:
#                 self._send(rec)

#             logger.info(f"   • page {params['page[number]']} → {len(data)} rec")
#             if len(data) < self.page_size:
#                 break
#             params["page[number]"] += 1

#         if self.enable_kafka:
#             self.producer.flush()
#         logger.info(f"[✓] {state} extraction complete")


# def main():
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--state", help="Single state to extract")
#     parser.add_argument("--all", action="store_true", help="Extract all states")
#     parser.add_argument("--no-kafka", action="store_true", help="Disable Kafka output")
#     parser.add_argument("--no-address", action="store_true", help="Disable reverse-geocoding/address enrichment")
#     args = parser.parse_args()

#     extractor = CampgroundExtractor(
#         enable_kafka=not args.no_kafka,
#         enable_address=not args.no_address
#     )

#     states = [
#         "Alabama","Alaska","Arizona","Arkansas","California","Colorado",
#         "Connecticut","Delaware","Florida","Georgia","Hawaii","Idaho",
#         "Illinois","Indiana","Iowa","Kansas","Kentucky","Louisiana",
#         "Maine","Maryland","Massachusetts","Michigan","Minnesota",
#         "Mississippi","Missouri","Montana","Nebraska","Nevada",
#         "New Hampshire","New Jersey","New Mexico","New York",
#         "North Carolina","North Dakota","Ohio","Oklahoma","Oregon",
#         "Pennsylvania","Rhode Island","South Carolina","South Dakota",
#         "Tennessee","Texas","Utah","Vermont","Virginia","Washington",
#         "West Virginia","Wisconsin","Wyoming","District of Columbia"
#     ]

#     if args.state:
#         extractor.fetch_state(args.state)
#     elif args.all:
#         for st in states:
#             try:
#                 extractor.fetch_state(st)
#             except Exception as e:
#                 logger.error(f"{st} → {e}")
#     else:
#         parser.print_help()


# if __name__ == "__main__":
#     main()
