"""
Minimal FastAPI backend for the MVP demo.

Receives detections POSTed from live_detect.py, stores them in memory
(good enough for a demo), and lets you view them as a simple list or count.

Usage:
    pip install fastapi uvicorn
    uvicorn backend:app --reload --port 8000

Then run live_detect.py with:
    --log-url http://localhost:8000/detections

View logged detections any time at:
    http://localhost:8000/detections
    http://localhost:8000/summary
"""

from collections import Counter
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Marine Waste Detection - Demo Backend")

detections = []  # in-memory store, swap for Firebase/MongoDB later


class Detection(BaseModel):
    class_name: str
    confidence: float
    timestamp: str


@app.post("/detections")
def log_detection(det: Detection):
    detections.append(det.dict())
    return {"status": "logged", "total": len(detections)}


@app.get("/detections")
def list_detections():
    return detections[-50:]  # last 50, so the response stays small in a demo


@app.get("/summary")
def summary():
    counts = Counter(d["class_name"] for d in detections)
    return {"total_detections": len(detections), "by_class": dict(counts)}