from datetime import datetime, timedelta
import os
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator

# ---------------------------------------------------------------------------
# DAG: fastapi_health_check
# Description: Curl the FastAPI instance that *lives on the HOST machine*
#              (outside the docker‑compose stack) once every hour.
#
# Docker‑for‑Linux not exposing the special DNS name `host.docker.internal` by
# default is the usual pain‑point.  Two pragmatic work‑arounds are baked‑in:
#   1.  If you added
#         extra_hosts:
#           - "host.docker.internal:host-gateway"
#       to the Airflow services, then the hostname *does* resolve – keep using
#       it.
#   2.  If you did **not** add the line above, the container can still reach the
#       host via the default bridge‑gateway IP **172.17.0.1**.
#
# You can therefore steer the task with the optional environment variable
# ``FASTAPI_HOST``.  When unset we try `host.docker.internal` *first* and fall
# back to `172.17.0.1`, so nothing else has to change on your side.
# ---------------------------------------------------------------------------

# Default arguments for retry behaviour
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


def _detect_host() -> str:
    """Figure‑out which host/IP we should talk to.

    Priority:
      1. FASTAPI_HOST   → user override
      2. host.docker.internal (works on Docker Desktop or when extra_hosts added)
      3. 172.17.0.1     → default bridge‑gateway on Linux
    """

    override = os.getenv("FASTAPI_HOST")
    if override:
        return override

    # Quick connectivity probe – try the nice hostname first
    test_url = "http://host.docker.internal:8000/health"
    try:
        requests.get(test_url, timeout=2)
        return "host.docker.internal"
    except Exception:
        return "172.17.0.1"  # last resort on plain Docker‑for‑Linux


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
        # Raise a hard error so the task is marked as failed/retry
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

    check_fastapi  # single‑task DAG
