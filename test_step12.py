# test_step12.py (temporary)
from database.crud import get_all_zones
from dashboard.map import build_hotspot_map

zones = get_all_zones()
print("Zones found:", len(zones))
fmap = build_hotspot_map(zones)
fmap.save("outputs/test_map.html")
print("Map saved to outputs/test_map.html - open it in a browser to check markers.")
