# analysis/risk.py
"""
Transparent, rule-based PRELIMINARY risk classification.
This is a prototype heuristic based on detection count/density/trend —
NOT a scientific or environmental risk assessment. All thresholds live
in config.RISK_THRESHOLDS so they can be tuned without touching logic.
"""

import math
from config import RISK_THRESHOLDS, CLUSTERING_CONFIG



def _zone_area_km2():
    """Approximate a zone's area as a circle with the DBSCAN eps radius."""
    eps_km = CLUSTERING_CONFIG["eps_km"]
    return math.pi * (eps_km ** 2)


def classify_risk(current_count, trend, confidence_weighted_count=None):
    """
    Args:
        current_count: number of detections currently in the zone.
        trend: 'New' | 'Increasing' | 'Decreasing' | 'Stable'.
        confidence_weighted_count: optional sum of confidences instead of
            a raw count, to reduce the influence of low-confidence detections.

    Returns: 'LOW' | 'MEDIUM' | 'HIGH'
    """
    count_for_density = confidence_weighted_count if confidence_weighted_count is not None else current_count
    density = count_for_density / _zone_area_km2()

    if current_count >= RISK_THRESHOLDS["high_count"] or density >= RISK_THRESHOLDS["high_density_per_km2"]:
        level = "HIGH"
    elif current_count >= RISK_THRESHOLDS["medium_count"] or density >= RISK_THRESHOLDS["medium_density_per_km2"]:
        level = "MEDIUM"
    else:
        level = "LOW"

    # An increasing trend is an early warning — bump LOW to MEDIUM,
    # but never downgrade an already-HIGH zone.
    if trend == "Increasing" and level == "LOW":
        level = "MEDIUM"

    return level