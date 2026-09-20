# database/crud.py
"""
All SQL for the prototype lives here as plain functions — no ORM models,
so it stays easy to read: every function opens a connection, runs one
piece of SQL, and closes the connection.
"""

import json
from psycopg2.extras import execute_values
from database.connection import get_connection


def insert_detection(image_name, image_path, debris_type, confidence,
                      latitude, longitude, detected_at, location_name=None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO detections
                    (image_name, image_path, debris_type, confidence, latitude, longitude, location_name, detected_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (image_name, image_path, debris_type, confidence, latitude, longitude, location_name, detected_at))
            new_id = cur.fetchone()[0]
        conn.commit()
        return new_id
    finally:
        conn.close()


def insert_detections(detections):
    """Insert all detections in one PostgreSQL transaction."""
    if not detections:
        return []

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            rows = [
                (d["image_name"], d["image_path"], d["debris_type"], d["confidence"],
                 d["latitude"], d["longitude"], d.get("location_name"), d["detected_at"])
                for d in detections
            ]
            inserted = execute_values(cur, """
                INSERT INTO detections
                    (image_name, image_path, debris_type, confidence, latitude, longitude, location_name, detected_at)
                VALUES %s
                RETURNING id;
            """, rows, fetch=True)
        conn.commit()
        return [row[0] for row in inserted]
    finally:
        conn.close()


def get_all_detections():
    """Returns every detection as a plain list of dicts (used by DBSCAN in Step 7)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                  SELECT id, latitude, longitude, debris_type, confidence, zone_id,
                      COALESCE(location_name, latitude::TEXT || ',' || longitude::TEXT)
                FROM detections;
            """)
            rows = cur.fetchall()
        return [
            {"id": r[0], "latitude": r[1], "longitude": r[2],
             "debris_type": r[3], "confidence": float(r[4]), "zone_id": r[5],
             "location_name": r[6]}
            for r in rows
        ]
    finally:
        conn.close()
        

def update_detection_zone(detection_id, zone_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE detections SET zone_id = %s WHERE id = %s;", (zone_id, detection_id))
        conn.commit()
    finally:
        conn.close()


def upsert_zone(zone_id, centroid_lat, centroid_lon, total_count,
                 dominant_debris, class_breakdown, risk_level=None,
                 trend=None, recommendation=None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO zones
                    (zone_id, centroid_latitude, centroid_longitude, total_count,
                     dominant_debris, class_breakdown, risk_level, trend, recommendation, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (zone_id) DO UPDATE SET
                    centroid_latitude = EXCLUDED.centroid_latitude,
                    centroid_longitude = EXCLUDED.centroid_longitude,
                    total_count = EXCLUDED.total_count,
                    dominant_debris = EXCLUDED.dominant_debris,
                    class_breakdown = EXCLUDED.class_breakdown,
                    risk_level = COALESCE(EXCLUDED.risk_level, zones.risk_level),
                    trend = COALESCE(EXCLUDED.trend, zones.trend),
                    recommendation = COALESCE(EXCLUDED.recommendation, zones.recommendation),
                    last_updated = NOW();
            """, (zone_id, centroid_lat, centroid_lon, total_count, dominant_debris,
                  json.dumps(class_breakdown), risk_level, trend, recommendation))
        conn.commit()
    finally:
        conn.close()


def get_all_zones():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT zone_id, centroid_latitude, centroid_longitude, total_count,
                       dominant_debris, class_breakdown, risk_level, trend, recommendation, last_updated
                FROM zones ORDER BY zone_id;
            """)
            rows = cur.fetchall()
        return [
            {"zone_id": r[0], "centroid_latitude": r[1], "centroid_longitude": r[2],
             "total_count": r[3], "dominant_debris": r[4], "class_breakdown": r[5],
             "risk_level": r[6], "trend": r[7], "recommendation": r[8], "last_updated": r[9]}
            for r in rows
        ]
    finally:
        conn.close()
        
def get_latest_zone_history_count(zone_id):
    """Most recent stored count for a zone BEFORE this update, or None if the zone is new."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT count FROM zone_history
                WHERE zone_id = %s ORDER BY timestamp DESC LIMIT 1;
            """, (zone_id,))
            row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def insert_zone_history(zone_id, count):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO zone_history (zone_id, timestamp, count) VALUES (%s, NOW(), %s);
            """, (zone_id, count))
        conn.commit()
    finally:
        conn.close()


def get_zone_history(zone_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT timestamp, count FROM zone_history
                WHERE zone_id = %s ORDER BY timestamp ASC;
            """, (zone_id,))
            rows = cur.fetchall()
        return [{"timestamp": r[0], "count": r[1]} for r in rows]
    finally:
        conn.close()


def update_zone_recommendation(zone_id, recommendation, risk_level=None, trend=None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE zones
                SET recommendation = %s,
                    risk_level = COALESCE(%s, risk_level),
                    trend = COALESCE(%s, trend),
                    last_updated = NOW()
                WHERE zone_id = %s;
            """, (recommendation, risk_level, trend, zone_id))
        conn.commit()
    finally:
        conn.close()


def update_detection_location(detection_id, location_name):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE detections SET location_name = %s WHERE id = %s;",
                (location_name, detection_id),
            )
        conn.commit()
    finally:
        conn.close()