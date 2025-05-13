from fastapi import APIRouter
from sqlalchemy import create_engine, text
from src.configs.config import Config

cfg = Config()
engine = create_engine(cfg.database_url)
router = APIRouter()

@router.get("/top-commented")
def get_top_commented():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM casestudy.top_commented_campgrounds")).fetchall()
    return [dict(row._mapping) for row in result]

@router.get("/state-summary")
def get_state_summary():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM casestudy.state_rating_summary")).fetchall()
    return [dict(row._mapping) for row in result]

@router.get("/top-private")
def get_top_private():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM casestudy.top_private_camps")).fetchall()
    return [dict(row._mapping) for row in result]
