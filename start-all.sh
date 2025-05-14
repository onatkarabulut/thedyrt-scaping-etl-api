#!/bin/bash
set -e


#ENV_NAME="thedyrt-env"
#if conda env list | grep -q "^${ENV_NAME}[[:space:]]"; then
#    echo "Conda environment '$ENV_NAME' already exists."
#else
#    echo "Creating Conda environment '$ENV_NAME'"
#    conda env create -f environment.yml
#fi
#
#echo "=========================================="
#echo "Activating Conda environment '$ENV_NAME'"
#echo "=========================================="
#source "$(conda info --base)/etc/profile.d/conda.sh"
#conda activate "$ENV_NAME"

echo "=========================================="
echo "Starting Docker Compose"
echo "=========================================="
docker-compose up > logs/docker.log 2>&1 &

echo "=========================================="
echo "Waiting for services to initialize... (Around 60 seconds)"
sleep 60

echo "=========================================="
echo "Creating Kafka topics if not exists..."
echo "=========================================="
docker exec kafka-broker-1 kafka-topics --create \
  --topic thedyrt-raw \
  --partitions 2 \
  --replication-factor 2 \
  --bootstrap-server kafka-broker-1:9092

docker exec kafka-broker-1 kafka-topics --create \
  --topic thedyrt-enriched \
  --partitions 2 \
  --replication-factor 2 \
  --bootstrap-server kafka-broker-1:9092




echo "=========================================="
echo "Listing Kafka topics"
echo "=========================================="
docker exec kafka-broker-1 kafka-topics --list --bootstrap-server kafka-broker-1:9092


echo "=========================================="
echo "Starting FastAPI server"
echo "=========================================="
sudo mkdir -p logs/kafka_logs logs/api_logs
sudo chmod -R 755 logs
fastapi run api/app.py --reload > logs/api_logs/api.log 2>&1 &




echo "🔄 Starting pipeline components..."

echo "=========================================="
echo "Starting Kafka pipeline components"
echo "=========================================="
nohup python3 -m src.pipeline.extract > logs/kafka_logs/extract.log 2>&1 &
nohup python3 -m src.pipeline.transform > logs/kafka_logs/transform.log 2>&1 &
nohup python3 -m src.pipeline.load > logs/kafka_logs/load.log 2>&1 &


echo "✅ Kafka pipeline is up and running."

exec python main.py
