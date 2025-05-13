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
    """Curl ``/health`` and fail the task if the endpoint is down."""

    host = _detect_host()
    port = os.getenv("FASTAPI_PORT", "8000")
    url = f"http://{host}:{port}/health"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        print("FastAPI health OK →", response.text)
    except Exception as exc:
        raise RuntimeError(f"Failed to reach FastAPI at {url}: {exc}") from exc


with DAG(
    dag_id="fastapi_health_check",
    default_args=default_args,
    description="Ping the host FastAPI /health endpoint every hour",
    schedule_interval="@hourly",
    start_date=datetime(2025, 5, 13),
    catchup=False,
    tags=["fastapi", "health"],
) as dag:

    check_fastapi = PythonOperator(
        task_id="check_fastapi",
        python_callable=check_fastapi_health,
    )

    check_fastapi

