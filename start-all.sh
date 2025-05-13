#!/usr/bin/env bash
# set -e

# echo "🛠  Starting Zookeeper & Kafka brokers..."
# docker-compose up -d zookeeper kafka-broker-1 kafka-broker-2

# echo "⏳  Waiting for Kafka to settle..."
# sleep 15

# echo "🗒️  Creating Kafka topics..."
# # raw veriyi extract.py → thedrt (RAW_TOPIC) olarak atıyor
# docker exec kafka-broker-1 kafka-topics --bootstrap-server kafka-broker-1:9092 \
#   --create --topic thedrt --partitions 3 --replication-factor 1 \
#   --if-not-exists

# # transform.py sonuçları thedrt-enriched (ENRICHED_TOPIC) olarak atıyor
# docker exec kafka-broker-1 kafka-topics --bootstrap-server kafka-broker-1:9092 \
#   --create --topic thedrt-enriched --partitions 3 --replication-factor 1 \
#   --if-not-exists

source activate test_env

# echo "📦  Launching Extractor (produce → thedrt)…"
# python3 -m src.pipeline.extract --all &> logs/kafka_logs/extract.log &

echo "🔄  Launching Transformer (consume thedrt → produce thedrt-enriched)…"
python3 -m src.pipeline.transform &> logs/kafka_logs/transform.log &

echo "💾  Launching Loader (consume thedrt-enriched → upsert DB)…"
python3 -m src.pipeline.load &> logs/kafka_logs/load.log &

echo "✅  All kafka pipeline started. Logs are under logs/kafka_logs/*.log"

docker exec -it airflow-scheduler bash
pip3 install reverse-geocode