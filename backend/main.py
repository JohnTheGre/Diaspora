from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import engine, SessionLocal, Base
import models
import os

LANGUAGE_THRESHOLD = 20.0
Base.metadata.create_all(bind=engine)

app = FastAPI()
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"status": "backend is running"}

@app.get("/api/height")
def get_height_data(db: Session = Depends(get_db)):
    countries = db.query(models.Country).filter(models.Country.avg_height_cm.isnot(None)).all()
    return [{"iso_code": c.iso_code, "name": c.name, "value": c.avg_height_cm} for c in countries]

@app.get("/api/weight")
def get_weight_data(db: Session = Depends(get_db)):
    countries = db.query(models.Country).filter(models.Country.avg_weight_kg.isnot(None)).all()
    return [{"iso_code": c.iso_code, "name": c.name, "value": c.avg_weight_kg} for c in countries]

@app.get("/api/language/{lang}")
def get_language_data(lang: str, min_percent: float = LANGUAGE_THRESHOLD, db: Session = Depends(get_db)):
    rows = (
        db.query(models.LanguageSpeakers)
        .filter(
            models.LanguageSpeakers.language.ilike(f"%{lang}%"),
            models.LanguageSpeakers.percentage > min_percent,
        )
        .all()
    )
    best = {}  # one entry per country, keeping the highest percentage
    for r in rows:
        iso = r.country.iso_code
        if iso not in best or r.percentage > best[iso]["value"]:
            best[iso] = {"iso_code": iso, "name": r.country.name, "value": r.percentage}
    return list(best.values())


@app.get("/api/diaspora/{origin_iso3}")
def get_diaspora_data(
    origin_iso3: str,
    min_population: int = 0,
    include_candidates: bool = False,
    db: Session = Depends(get_db)
):
    origin_iso3 = origin_iso3.strip().upper()

    query = db.query(models.DiasporaPopulation).filter(
        models.DiasporaPopulation.origin_iso3 == origin_iso3
    )

    # By default, only return records with a known population estimate.
    if not include_candidates:
        query = query.filter(
            models.DiasporaPopulation.population_count.isnot(None)
        )

    if min_population > 0:
        query = query.filter(
            models.DiasporaPopulation.population_count >= min_population
        )

    rows = query.all()

    return [
        {
            "iso_code": row.destination_iso3,
            "name": row.destination_country,
            "value": row.population_count,
            "status": row.record_status,
            "estimate_year": row.estimate_year,
            "confidence": row.confidence,
            "source_url": row.source_url,
        }
        for row in rows
    ]

@app.get("/api/languages")
def list_languages(db: Session = Depends(get_db)):
    count = func.count(models.LanguageSpeakers.country_id)
    rows = (
        db.query(models.LanguageSpeakers.language, count)
        .group_by(models.LanguageSpeakers.language)
        .order_by(count.desc(), models.LanguageSpeakers.language)
        .all()
    )
    return [{"language": lang, "countries": n} for lang, n in rows]


@app.get("/api/diaspora-origins")
def list_diaspora_origins(db: Session = Depends(get_db)):
    rows = (
        db.query(
            models.DiasporaPopulation.origin_iso3,
            models.DiasporaPopulation.origin_country,
        )
        .distinct()
        .order_by(models.DiasporaPopulation.origin_country)
        .all()
    )
    return [{"iso": iso, "name": name} for iso, name in rows]

@app.get("/api/countries")
def list_countries(db: Session = Depends(get_db)):
    rows = db.query(models.Country).order_by(models.Country.name).all()
    return [{"iso": c.iso_code, "name": c.name} for c in rows]