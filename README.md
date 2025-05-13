# 🏕️ The Dyrt ETL & Analytics Platform

> A fully automated data pipeline for scraping, enriching, and analyzing campground data from [TheDyrt.com](https://thedyrt.com).  
> Powered by Kafka, PostgreSQL, FastAPI, and a custom SQL-driven analytics layer.

---

## 🧠 Architecture

```mermaid
graph TD
    Scraper[Web Scraper] --> KafkaRaw[Kafka Topic: thedyrt-raw]
    KafkaRaw --> Transformer[Transformer]
    Transformer --> KafkaEnriched[Kafka Topic: thedyrt-enriched]
    KafkaEnriched --> Loader[Loader (Upsert to PostgreSQL)]
    PostgreSQL --> Views[Materialized Views / SQL Analytics]
    FastAPI[FastAPI Backend] -->|REST APIs| Users
    Users -->|Query Views| Views
    Users -->|Trigger ETL| FastAPI
```
🧱 Tech Stack

    Web Scraping: httpx + async parsing from map-based endpoint

    Kafka Topics: thedyrt-raw, thedyrt-enriched

    Database: PostgreSQL (casestudy schema)

    ETL Framework: Producer/Consumer modules (extract / transform / load)

    API Layer: FastAPI – analytics & pipeline control

    SQL Analytics: Views like top_commented_campgrounds, state_rating_summary, top_private_camps


🚀 Getting Started
1. Clone & Setup

git clone https://github.com/yourusername/case_study.git
cd case_study
cp example.env .env

2. Start Everything

bash start-all.sh

This will:

    Run Docker services

    Create Kafka topics

    Launch FastAPI

    Start all ETL modules
📡 API Endpoints
🔁 Pipeline Control
| Method | Endpoint                  | Description                  |
| ------ | ------------------------- | ---------------------------- |
| `POST` | `/Pipeline/run-extract`   | Run extractor manually       |
| `POST` | `/Pipeline/run-transform` | Trigger transformation       |
| `POST` | `/Pipeline/run-load`      | Load enriched data to DB     |
| `GET`  | `/Pipeline/status`        | Check if processes are alive |
| `GET`  | `/Pipeline/logs/{step}`   | Retrieve log file content    |


📊 SQL View Analytics
| Endpoint               | Description                      |
| ---------------------- | -------------------------------- |
| `/Views/top-commented` | Top 10 most reviewed campgrounds |
| `/Views/state-summary` | Avg price, rating per state      |
| `/Views/top-private`   | Best-performing private camps    |


🔎 SQL Query APIs
| Endpoint                             | Description                       |
| ------------------------------------ | --------------------------------- |
| `/DB/campgrounds?state=AL&name=lake` | Filter by state/name              |
| `/DB/campgrounds/top10-states`       | Highest campground density        |
| `/DB/campgrounds/avg-price-by-state` | Price insights per state          |
| `/DB/campgrounds/by-state/{state}`   | Detailed campgrounds in one state |


---

<!-- THIS PROJECT IS NOT COMPLETED YET -->
# Web-Scrape Case Study

## Overview
Develop a scraper to extract all campground locations across the United States from The Dyrt https://thedyrt.com/search by leveraging their map interface which exposes latitude/longitude data through API requests when the mouse moves. You're free to use any library you want (requests, httpx, selenium, playwright)
For questions please connect us via email at info@smart-maple.com

**Hint:** Look for a search endpoint in the network tab!

## Core Requirements
- We provided a Docker compose file, you need to connect to PostgreSQL, create the necessary fields/tables (15p)
- Scrape all campground data from the US map interface and store it in the database (30p)
- Validate the data with pydantic, you can check the necessary fields from src/models/campground.py (these fields are the required fields to store in the db) (15p)
- Scheduling: Cron-like scheduling for regular updates (15p)
- Update: update existing records if they exist. (10p)
- Error handling: handle errors in your code, especially HTTP errors, aand add retries if necessary (15p)

## Bonus
- Database: Use an ORM for PostgreSQL operations
- Logging: Comprehensive logging system
- API Endpoint: Flask/FastAPI endpoint to trigger/control scraper 
  (Hint: you can implement this in an async fashion)
- Performance: Multithreading/async implementation
- Find address from lat/long field
- Feel free to use your creativity every additional field is appreciated

