# dashboard/map.py
"""
Renders zones as an interactive Folium map, color-coded by risk level.
This map shows uploaded/demo-assigned coordinates — it does NOT imply
real-time physical monitoring of an actual site.
"""

import folium

RISK_COLORS = {
    "LOW": "green",
    "MEDIUM": "orange",
    "HIGH": "red",
}


def build_hotspot_map(zones):
    """
    Args:
        zones: list of zone dicts from database.crud.get_all_zones()
               (each with centroid_latitude, centroid_longitude, risk_level,
               total_count, dominant_debris, zone_id).

    Returns:
        a folium.Map object, ready to render with streamlit_folium.
    """
    if not zones:
        return folium.Map(location=[0, 0], zoom_start=2)

    avg_lat = sum(z["centroid_latitude"] for z in zones) / len(zones)
    avg_lon = sum(z["centroid_longitude"] for z in zones) / len(zones)

    fmap = folium.Map(location=[avg_lat, avg_lon], zoom_start=13)

    for z in zones:
        color = RISK_COLORS.get(z["risk_level"], "gray")
        popup_html = (
            f"<b>{z['zone_id']}</b><br>"
            f"Risk: {z['risk_level']}<br>"
            f"Count: {z['total_count']}<br>"
            f"Dominant debris: {z['dominant_debris']}<br>"
            f"Trend: {z['trend']}"
        )
        folium.CircleMarker(
            location=[z["centroid_latitude"], z["centroid_longitude"]],
            radius=8 + min(z["total_count"], 50) / 5,  # bigger marker for higher counts, capped
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{z['zone_id']} — {z['risk_level']}",
        ).add_to(fmap)

    return fmap