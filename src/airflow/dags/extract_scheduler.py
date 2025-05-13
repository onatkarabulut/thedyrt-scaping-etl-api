from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import requests
import logging

from pathlib import Path
import sys
dag_path = Path(__file__).parent.absolute()
project_root = dag_path.parent.parent  # src klasörüne ulaşmak için
sys.path.insert(0, str(project_root))

# Artık src modülünü import edebilirsiniz
from src.pipeline.extract import main as extract_main

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=10)
}

def call_api():
    import os
    logging.info(f"Current working directory: {os.getcwd()}")

with DAG(
    'api_pipeline_integration',
    default_args=default_args,
    schedule_interval='*/20 * * * *',  # Her 20 dakikada bir
    catchup=False,
    max_active_runs=1,
    tags=['api', 'pipeline']
) as dag:
    
    api_call_task = PythonOperator(
        task_id='call_api_endpoint',
        python_callable=call_api,
    )
