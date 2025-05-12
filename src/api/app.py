# src/api/main.py
from fastapi import FastAPI
from src.api.services.etl import extract, transform, load

app = FastAPI(
    title="Campground ETL API",
    description="Extract ↔ Transform ↔ Load pipeline endpoints + analytics",
    version="1.0.0",
)

app.include_router(extract.router, prefix="/extract", tags=["extract"])
app.include_router(transform.router, prefix="/transform", tags=["transform"])
app.include_router(load.router, prefix="/load", tags=["load"])
