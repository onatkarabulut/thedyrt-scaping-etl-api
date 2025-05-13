from fastapi import APIRouter, HTTPException
import subprocess
import os

etl = APIRouter()

LOG_DIR = "logs/kafka_logs"

@etl.post("/run-extract")
def run_extract():
    """Tüm extract işlemini çalıştır"""
    result = subprocess.run(
        ["python", "-m", "src.pipeline.extract", "--all"],
        capture_output=True,
        text=True
    )
    return {
        "success": result.returncode == 0,
        "output": result.stdout,
        "error": result.stderr
    }

@etl.post("/run-transform")
def run_transform():
    """Transform işlemini çalıştır"""
    result = subprocess.run(
        ["python", "-m", "src.pipeline.transform"],
        capture_output=True,
        text=True
    )
    return {
        "success": result.returncode == 0,
        "output": result.stdout,
        "error": result.stderr
    }

@etl.post("/run-load")
def run_load():
    """Load işlemini çalıştır"""
    result = subprocess.run(
        ["python", "-m", "src.pipeline.load"],
        capture_output=True,
        text=True
    )
    return {
        "success": result.returncode == 0,
        "output": result.stdout,
        "error": result.stderr
    }

@etl.get("/status")
def pipeline_status():
    """extract / transform / load script'lerinin çalışıp çalışmadığını kontrol eder"""
    processes = subprocess.run(
        ["ps", "aux"], capture_output=True, text=True
    ).stdout

    def is_running(name): return name in processes

    return {
        "extract": is_running("src.pipeline.extract"),
        "transform": is_running("src.pipeline.transform"),
        "load": is_running("src.pipeline.load")
    }

@etl.get("/logs/{step}")
def get_log(step: str):
    """İlgili pipeline adımının log dosyasını getirir"""
    valid_steps = ["extract", "transform", "load"]
    if step not in valid_steps:
        raise HTTPException(status_code=400, detail="Geçersiz adım adı.")

    log_path = os.path.join(LOG_DIR, f"{step}.log")
    if not os.path.exists(log_path):
        raise HTTPException(status_code=404, detail="Log dosyası bulunamadı.")

    with open(log_path, "r") as file:
        content = file.read()

    return {"step": step, "log": content}
