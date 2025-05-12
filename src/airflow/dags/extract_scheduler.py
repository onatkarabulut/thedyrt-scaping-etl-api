# src/airlow/dags/campgrounds_etl.py
from airflow import DAG
from airflow.providers.apache.kafka.sensors.kafka import KafkaSensor
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime, timedelta

from src.pipeline.extract import CampgroundExtractor
from src.pipeline.transform import transform_batch
from src.pipeline.load import load_to_db

default_args = {
    "owner": "etl",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="campgrounds_etl",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule_interval="0 * * * *",
    catchup=False,
    tags=["campgrounds", "kafka"],
) as dag:

    def extract(**ctx):
        extractor = CampgroundExtractor(enable_kafka=True, enable_address=True)
        # örneğin tüm eyaletleri ardışık çek
        for st in cfg.api["states"]:
            extractor.fetch_state(st)

    extract_task = PythonOperator(
        task_id="extract",
        python_callable=extract,
        provide_context=True,
    )

    wait_kafka = KafkaSensor(
        task_id="wait_for_raw",
        kafka_conn_id="kafka_default",
        topic="thedyrt-raw",
        group_id="etl_transformer",
        timeout=600,
        poke_interval=30,
        mode="reschedule",
    )

    def transform(**ctx):
        # raw topic’dan oku, pyspark veya pandas ile dönüştür
        transform_batch(source_topic="thedyrt-raw", target_topic="thedyrt-transformed")

    transform_task = PythonOperator(
        task_id="transform",
        python_callable=transform,
        provide_context=True,
    )

    wait_transformed = KafkaSensor(
        task_id="wait_for_transformed",
        kafka_conn_id="kafka_default",
        topic="thedyrt-transformed",
        group_id="etl_loader",
        timeout=600,
        poke_interval=30,
        mode="reschedule",
    )

    load_task = PythonOperator(
        task_id="load",
        python_callable=lambda: load_to_db(topic="thedyrt-transformed"),
    )

    # DAG akışı
    extract_task >> wait_kafka >> transform_task >> wait_transformed >> load_task

