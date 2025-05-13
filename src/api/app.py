from fastapi import FastAPI
from src.api.services.etl import etl
from src.api.services.views import router as views_router
from src.api.services.db import router as db_router

app = FastAPI(
    title="Campground ETL API",
    description="Extract ↔ Transform ↔ Load pipeline endpoints + analytics",
    version="1.0.0",
)

app.include_router(etl, prefix="/Pipeline", tags=["RUN"])
app.include_router(views_router, prefix="/Views", tags=["SQL View Analytics"])
app.include_router(db_router, prefix="/DB", tags=["Custom SQL Queries"])
