from database.crud import get_all_detections
from clustering.dbscan import run_clustering
from analysis.zone_statistics import generate_zones_from_clusters
from config import CLUSTERING_CONFIG

points = get_all_detections()
result = run_clustering(points, **CLUSTERING_CONFIG)
zones = generate_zones_from_clusters(result["clusters"])

for z in zones:
    llm = z["llm_analysis"]
    print(z["zone_id"], "source:", llm["source"])
    print("  ", llm["cleanup_recommendation"])
