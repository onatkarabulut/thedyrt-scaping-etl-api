from fastapi import FastAPI
import subprocess

app = FastAPI()

@app.post("/run-extract")
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

@app.get("/health")
def health_check():
    return {"status": "healthy"}