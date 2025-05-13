import os
import shutil
import subprocess
import time

def copy_env_file():
    old_name = "example.env"
    new_name = ".env"
    if os.path.exists(old_name) and not os.path.exists(new_name):
        shutil.copyfile(old_name, new_name)
        print(f"✅ '{old_name}' dosyası '{new_name}' olarak kopyalandı.")
    else:
        print("⚠️ '.env' zaten var veya 'example.env' bulunamadı.")

def start_docker_compose():
    print("==========================================")
    print("Starting Docker Compose in detached mode")
    print("==========================================")
    os.makedirs("logs", exist_ok=True)
    with open("logs/docker.log", "w") as f:
        subprocess.Popen(
            ["sudo", "docker-compose", "up"],
            stdout=f,
            stderr=subprocess.STDOUT
        )
    print("⌛ Waiting for services to initialize (60s)...")
    time.sleep(60)

def create_kafka_topics():
    print("==========================================")
    print("Creating Kafka topics if not exists...")
    print("==========================================")
    topics = [
        ("thedyrt-enriched", 3),
        ("thedyrt-raw", 3),
    ]
    for topic, partitions in topics:
        subprocess.run([
            "docker", "exec", "kafka-broker-1",
            "kafka-topics",
            "--bootstrap-server", "kafka-broker-1:9092",
            "--create",
            "--if-not-exists",
            "--topic", topic,
            "--partitions", str(partitions),
            "--replication-factor", "1"
        ], check=False)

def list_kafka_topics():
    print("==========================================")
    print("Listing Kafka topics")
    print("==========================================")
    subprocess.run([
        "sudo", "docker", "exec", "kafka-broker-1",
        "kafka-topics", "--list", "--bootstrap-server", "kafka-broker-1:9092"
    ])

def start_fastapi_server():
    print("==========================================")
    print("Starting FastAPI server")
    print("==========================================")
    os.makedirs("logs/api_logs", exist_ok=True)
    with open("logs/api_logs/api.log", "w") as f:
        subprocess.Popen(
            ["python3", "-m", "src.api.app"],
            stdout=f,
            stderr=subprocess.STDOUT
        )

def start_kafka_pipeline():
    print("🔄 Starting pipeline components...")
    os.makedirs("logs/kafka_logs", exist_ok=True)

    components = {
        "extract": "src.pipeline.extract",
        "transform": "src.pipeline.transform",
        "load": "src.pipeline.load",
    }

    for name, module in components.items():
        log_path = f"logs/kafka_logs/{name}.log"
        with open(log_path, "w") as f:
            subprocess.Popen(
                ["python3", "-m", module],
                stdout=f,
                stderr=subprocess.STDOUT
            )
    print("✅ Kafka pipeline is up and running.")

def main():
    copy_env_file()
    start_docker_compose()
    create_kafka_topics()
    list_kafka_topics()
    start_fastapi_server()
    start_kafka_pipeline()

if __name__ == "__main__":
    main()
