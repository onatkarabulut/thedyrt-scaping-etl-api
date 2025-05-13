from fastapi import APIRouter, Query
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from src.configs.config import Config
from pathlib import Path

cfg = Config()
DATABASE_URL = cfg.database_url
engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

router = APIRouter()
SQL_DIR = Path(__file__).resolve().parent.parent.parent / "sql"

def run_sql(filename: str, params: dict = None):
    db = SessionLocal()
    with open(SQL_DIR / filename, encoding="utf-8") as f:
        query = text(f.read())
        result = db.execute(query, params or {})
        return [dict(row) for row in result]

@router.get("/campgrounds")
def list_campgrounds(state: str = Query(None), name: str = Query(None)):
    db = SessionLocal()
    sql = "SELECT * FROM campground_all"
    conditions = []
    params = {}
    if state:
        conditions.append("state = :state")
        params["state"] = state
    if name:
        conditions.append("LOWER(name) LIKE :name")
        params["name"] = f"%{name.lower()}%"
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    result = db.execute(text(sql), params)
    return [dict(row) for row in result]

@router.get("/campgrounds/top10-states")
def top_states():
    return run_sql("top_10_states.sql")

@router.get("/campgrounds/avg-price-by-state")
def avg_price():
    return run_sql("avg_price_by_state.sql")

@router.get("/campgrounds/by-state/{state}")
def campgrounds_by_state(state: str):
    return run_sql("campground_by_state.sql", {"state": state})
