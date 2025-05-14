from datetime import datetime, timedelta
import os
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

def _detect_host() -> str:
    override = os.getenv("FASTAPI_HOST")
    if override:
        return override

    test_url = "http://host.docker.internal:8000/health"
    try:
        requests.get(test_url, timeout=2)
        return "host.docker.internal"
    except Exception as e:
        return str(e)

def check_fastapi_health() -> None:
    host = _detect_host()
    port = os.getenv("FASTAPI_PORT", "8000")
    url = f"http://{host}:{port}/health"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        print("✅ FastAPI health OK:", response.text)
    except Exception as exc:
        raise RuntimeError(f"❌ FastAPI health check failed: {url}: {exc}") from exc

def trigger_run_extract() -> None:
    host = _detect_host()
    port = os.getenv("FASTAPI_PORT", "8000")
    url = f"http://{host}:{port}/Pipeline/run-extract"

    try:
        response = requests.post(url, timeout=15)
        response.raise_for_status()
        print("✅ Extract triggered successfully:", response.json())
    except Exception as exc:
        raise RuntimeError(f"❌ Failed to trigger extract: {url}: {exc}") from exc

with DAG(
    dag_id="fastapi_health_check",
    default_args=default_args,
    description="Ping FastAPI /health and trigger /Pipeline/run-extract",
    schedule_interval="@hourly",
    start_date=datetime(2025, 5, 13),
    catchup=False,
    tags=["fastapi", "health", "etl"],
) as dag:

    health_check = PythonOperator(
        task_id="check_fastapi",
        python_callable=check_fastapi_health,
    )

    run_extract = PythonOperator(
        task_id="trigger_run_extract",
        python_callable=trigger_run_extract,
    )

    health_check >> run_extract
