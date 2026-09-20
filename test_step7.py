from database.crud import get_all_detections
from clustering.dbscan import run_clustering
from config import CLUSTERING_CONFIG

points = get_all_detections()
print(f"Total detections: {len(points)}")

result = run_clustering(points, **CLUSTERING_CONFIG)
print(f"Clusters found: {len(result['clusters'])}")
for label, pts in result["clusters"].items():
    print(f"  Cluster {label}: {len(pts)} points")
print(f"Noise (unclustered) points: {len(result['noise'])}")
