# analysis/zone_statistics.py
"""
Turns DBSCAN clusters into named zones and computes zone-level statistics.
All numbers here are calculated in Python from the database — nothing is
estimated or invented by an LLM (that comes later, in Step 11, purely as
an interpretation layer over these numbers).
"""

import math
from collections import Counter
from analysis.ollama import get_zone_analysis

from clustering.dbscan import compute_centroid
from database import crud
from config import ZONE_MATCH_TOLERANCE_KM
from clustering.dbscan import compute_centroid
from database import crud
from config import ZONE_MATCH_TOLERANCE_KM
from analysis.risk import classify_risk

EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(min(1, math.sqrt(a)))


def _match_existing_zone(centroid_lat, centroid_lon, candidate_zones):
    """Find the closest existing zone within tolerance, so the same
    real-world hotspot keeps the same zone_id across clustering runs."""
    best_zone, best_dist = None, None
    for z in candidate_zones:
        dist = haversine_km(centroid_lat, centroid_lon, z["centroid_latitude"], z["centroid_longitude"])
        if dist <= ZONE_MATCH_TOLERANCE_KM and (best_dist is None or dist < best_dist):
            best_zone, best_dist = z["zone_id"], dist
    return best_zone


def _location_id(points, centroid_lat, centroid_lon):
    """Use the saved location as the zone ID source."""
    labels = [p.get("location_name") for p in points if p.get("location_name")]
    if labels:
        return "".join(char for char in labels[0].strip().upper() if char.isalnum())
    return f"{centroid_lat:.6f}_{centroid_lon:.6f}"


def _next_zone_id(existing_zone_ids, location_id):
    """Return the location ID, adding a suffix only for another same-location zone."""
    if location_id not in existing_zone_ids:
        return location_id

    suffix = 2
    while f"{location_id}-{suffix}" in existing_zone_ids:
        suffix += 1
    return f"{location_id}-{suffix}"


def generate_zones_from_clusters(clusters):
    """
    Args:
        clusters: {cluster_label: [detection dicts]} from clustering.dbscan.run_clustering()

    Returns:
        list of zone summary dicts. Also persists: zones table, detections.zone_id,
        and zone_history.
    """
    existing_zones = crud.get_all_zones()
    assigned_ids = []
    summaries = []

    for _, points in clusters.items():
        centroid_lat, centroid_lon = compute_centroid(points)

        zone_id = _match_existing_zone(centroid_lat, centroid_lon, existing_zones)
        if zone_id is None:
            zone_id = _next_zone_id(
                [z["zone_id"] for z in existing_zones] + assigned_ids,
                _location_id(points, centroid_lat, centroid_lon),
            )
        assigned_ids.append(zone_id)

        debris_counter = Counter(p["debris_type"] for p in points)
        dominant_debris = debris_counter.most_common(1)[0][0]
        current_count = len(points)

        # --- Step 9: history + trend ---
        previous_count = crud.get_latest_zone_history_count(zone_id)
        trend = calculate_trend(current_count, previous_count)
        change = None if previous_count is None else current_count - previous_count
        pct_change = None if not previous_count else round((change / previous_count) * 100, 1)

        # --- Step 10: risk classification ---
        risk_level = classify_risk(current_count, trend)

        for p in points:
            crud.update_detection_zone(p["id"], zone_id)

        crud.upsert_zone(
            zone_id=zone_id,
            centroid_lat=centroid_lat,
            centroid_lon=centroid_lon,
            total_count=current_count,
            dominant_debris=dominant_debris,
            class_breakdown=dict(debris_counter),
            risk_level=risk_level,
            trend=trend,
        )

        crud.insert_zone_history(zone_id, current_count)
        

        summaries.append({
            "zone_id": zone_id,
            "centroid_latitude": centroid_lat,
            "centroid_longitude": centroid_lon,
            "current_count": current_count,
            "previous_count": previous_count,
            "change": change,
            "pct_change": pct_change,
            "trend": trend,
            "risk_level": risk_level,
            "dominant_debris": dominant_debris,
            "class_breakdown": dict(debris_counter),
        })

        # --- Step 11: Ollama interpretation of the already-calculated stats ---
        llm_result = get_zone_analysis(summaries[-1])
        crud.update_zone_recommendation(zone_id, llm_result["cleanup_recommendation"])
        summaries[-1]["llm_analysis"] = llm_result

    

    return summaries
def calculate_trend(current_count, previous_count):
    """Returns 'New' | 'Increasing' | 'Decreasing' | 'Stable' based on % change."""
    if previous_count is None:
        return "New"
    if previous_count == 0:
        return "Increasing" if current_count > 0 else "Stable"

    pct_change = ((current_count - previous_count) / previous_count) * 100
    if pct_change > 10:
        return "Increasing"
    elif pct_change < -10:
        return "Decreasing"
    return "Stable"