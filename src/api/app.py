from fastapi import FastAPI
from src.api.services import etl

app = FastAPI(
    title="Campground ETL API",
    description="Extract ↔ Transform ↔ Load pipeline endpoints + analytics",
    version="1.0.0",
)

app.include_router(etl, prefix="/Pipeline", tags=["RUN"])
