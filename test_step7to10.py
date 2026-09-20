# test_step7to10.py (temporary)
from database.crud import get_all_detections
from clustering.dbscan import run_clustering
from analysis.zone_statistics import generate_zones_from_clusters
from config import CLUSTERING_CONFIG

points = get_all_detections()
print(f"Total detections in DB: {len(points)}")

result = run_clustering(points, **CLUSTERING_CONFIG)
print(f"Clusters: {len(result['clusters'])}, Noise points: {len(result['noise'])}")

zones = generate_zones_from_clusters(result["clusters"])
for z in zones:
    print(f"\n{z['zone_id']}  risk={z['risk_level']}  trend={z['trend']}")
    print(f"  current={z['current_count']} previous={z['previous_count']} change={z['change']}")
    print(f"  dominant={z['dominant_debris']}  breakdown={z['class_breakdown']}")
