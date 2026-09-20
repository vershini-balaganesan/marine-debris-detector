# clustering/dbscan.py
"""
Groups nearby detections into spatial clusters using DBSCAN with a
haversine distance metric (true geographic distance), not raw
Euclidean distance on lat/lon degrees.
"""

import numpy as np
from sklearn.cluster import DBSCAN

EARTH_RADIUS_KM = 6371.0


def run_clustering(points, eps_km, min_samples):
    """
    Args:
        points: list of dicts with 'id', 'latitude', 'longitude'
                (as returned by database.crud.get_all_detections()).
        eps_km: DBSCAN neighborhood radius, in kilometers.
        min_samples: DBSCAN minimum samples per dense region.

    Returns:
        {
          "clusters": {cluster_label: [point, ...]},
          "noise": [point, ...]   # unclustered points — NOT turned into zones
        }
    """
    if len(points) < min_samples:
        # Not enough points in the whole dataset to form even one cluster.
        return {"clusters": {}, "noise": points}

    coords_deg = np.array([[p["latitude"], p["longitude"]] for p in points])
    coords_rad = np.radians(coords_deg)
    eps_rad = eps_km / EARTH_RADIUS_KM  # convert km radius -> radians for the haversine metric

    labels = DBSCAN(eps=eps_rad, min_samples=min_samples, metric="haversine").fit_predict(coords_rad)

    clusters, noise = {}, []
    for point, label in zip(points, labels):
        if label == -1:
            noise.append(point)
        else:
            clusters.setdefault(int(label), []).append(point)

    return {"clusters": clusters, "noise": noise}


def compute_centroid(cluster_points):
    """Arithmetic mean centroid — a reasonable approximation for small, tight clusters."""
    lats = [p["latitude"] for p in cluster_points]
    lons = [p["longitude"] for p in cluster_points]
    return sum(lats) / len(lats), sum(lons) / len(lons)