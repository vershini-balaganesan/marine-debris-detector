# config.py
"""Central configuration for the application."""

import os


def _configured_database_url():
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url:
        return database_url

    try:
        import streamlit as st

        database_url = st.secrets.get("DATABASE_URL", "")
        if database_url:
            return str(database_url).strip()

        postgresql = st.secrets.get("connections", {}).get("postgresql", {})
        return str(postgresql.get("url", "")).strip()
    except Exception:
        return ""


_database_url = _configured_database_url()
_placeholder_hosts = {
    "actual-host",
    "real-host",
    "cloud.example",
    "db.example.com",
    "host",
    "your-real-postgresql-url",
}
_is_placeholder_url = any(host in _database_url for host in _placeholder_hosts)
DATABASE_URL = (
    _database_url
    if _database_url
    and not _is_placeholder_url
    and _database_url.lower() not in {
        "your-real-cloud-postgresql-url",
        "postgresql://user:password@host:5432/database?sslmode=require",
    }
    else None
)


# --- Database configuration ---
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "marine_debris"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "6682"),
}
# Max distance (km) between a new cluster's centroid and an existing zone's
# centroid for them to be considered "the same zone" across clustering runs.
ZONE_MATCH_TOLERANCE_KM = 0.3
# --- DBSCAN clustering configuration ---
# eps_km: the maximum distance (in km) between two points for them to be
#         considered neighbors of each other — roughly, the "radius" of a
#         cluster/hotspot.
# min_samples: the minimum number of detections needed to form a dense
#              region. A point with fewer than this many nearby neighbors
#              is treated as noise and NOT turned into a zone.
CLUSTERING_CONFIG = {
    "eps_km": 0.5,
    "min_samples": 3,
}
INSPECTION_CONFIG = {
    "max_nearby_zones": 10,
    "medium_detection_count": 5,
    "high_detection_count": 20,
    "medium_nearby_count": 40,
    "high_nearby_count": 100,
}
# --- Risk classification thresholds (rule-based PROTOTYPE only — not a
# scientific environmental risk model). Editable here without touching code.
RISK_THRESHOLDS = {
    "high_count": 100,
    "medium_count": 40,
    "high_density_per_km2": 200,     # detections per km^2 within the zone's eps radius
    "medium_density_per_km2": 80,
}
# --- Ollama configuration ---
OLLAMA_CONFIG = {
    "base_url": "http://localhost:11434",
    "model": "llama3.2:latest",   # change to whatever model you've pulled locally
    # Set OLLAMA_VISION_MODEL to a model such as llava:latest for image inspection.
    "vision_model": os.getenv("OLLAMA_VISION_MODEL", "").strip(),
    "timeout_seconds": 120,
}