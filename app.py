# app.py
"""
Marine Debris Detection Prototype — SOFTWARE-ONLY PROTOTYPE.

No physical camera or GPS hardware is used anywhere in this application.
Images are selected from the user's device/gallery; coordinates are entered
manually or chosen from demo/simulated locations. The same interface could
later receive coordinates from a GPS-enabled hardware platform.
"""

import os
import math
import streamlit as st
import pandas as pd
from streamlit_folium import st_folium

from ml.detector import run_inference
from database import crud
from clustering.dbscan import run_clustering
from analysis.zone_statistics import generate_zones_from_clusters
from analysis.ollama import ask_dashboard_chat
from dashboard.map import build_hotspot_map
from dashboard.charts import zone_history_dataframe
from dashboard.theme import apply_theme, badge, risk_badge
from dashboard.cards import mini_trend_chart, zone_count_bar_chart, zone_risk_chart
from config import CLUSTERING_CONFIG, INSPECTION_CONFIG
from location import geocode_place


def inspection_pollution_level(detection_count, nearby_zones):
    """Return a transparent image/area heuristic, not a scientific assessment."""
    nearby_count = sum(zone["count"] for zone in nearby_zones)
    highest_risk = {zone.get("risk", "LOW") for zone in nearby_zones}
    if (
        "HIGH" in highest_risk
        or detection_count >= INSPECTION_CONFIG["high_detection_count"]
        or nearby_count >= INSPECTION_CONFIG["high_nearby_count"]
    ):
        return "HIGH"
    if (
        "MEDIUM" in highest_risk
        or detection_count >= INSPECTION_CONFIG["medium_detection_count"]
        or nearby_count >= INSPECTION_CONFIG["medium_nearby_count"]
    ):
        return "MEDIUM"
    return "LOW" if detection_count or nearby_count else "NONE"

st.set_page_config(page_title="Marine Debris Detection Prototype", layout="wide")
apply_theme()

UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

page = st.sidebar.radio(
    "Navigate",
    ["Home / Dashboard", "Upload & Detect", "Hotspot Map", "Zone Analysis", "Detection History", "About / Methodology"],
)

# ---------------------------------------------------------------
# PAGE: Home / Dashboard
# ---------------------------------------------------------------
if page == "Home / Dashboard":
    st.title("🌊 Marine Debris Dashboard")

    try:
        detections = crud.get_all_detections()
        zones = crud.get_all_zones()
    except ConnectionError as e:
        st.error(f"Database unavailable: {e}")
        detections, zones = [], []

    from collections import Counter

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        with st.container(border=True):
            st.metric("Total Detections", len(detections))
            if zones:
                trend_values = [z["total_count"] for z in zones]
                st.pyplot(mini_trend_chart(trend_values), use_container_width=True)

    with c2:
        with st.container(border=True):
            st.metric("Number of Zones", len(zones))

    with c3:
        with st.container(border=True):
            high_risk = [z for z in zones if z["risk_level"] == "HIGH"]
            st.metric("High-Risk Zones", len(high_risk))

    with c4:
        with st.container(border=True):
            if detections:
                common = Counter(d["debris_type"] for d in detections).most_common(1)[0][0]
            else:
                common = "N/A"
            st.metric("Most Common Debris", common)

    st.write("")

    col_left, col_right = st.columns([2, 1])

    with col_left:
        with st.container(border=True):
            st.markdown('<div class="card-title">Detections by Zone</div>', unsafe_allow_html=True)
            if zones:
                labels = [z["zone_id"] for z in zones]
                counts = [z["total_count"] for z in zones]
                st.pyplot(zone_count_bar_chart(labels, counts), use_container_width=True)
            else:
                st.info("No zones yet — run clustering from the Hotspot Map page.")

    with col_right:
        with st.container(border=True):
            st.markdown('<div class="card-title">Zone Risk Overview</div>', unsafe_allow_html=True)
            if zones:
                st.pyplot(zone_risk_chart(zones), use_container_width=True)
            else:
                st.info("No zones available.")

    st.write("")

    with st.container(border=True):
        st.markdown('<div class="card-title">Zones Overview</div>', unsafe_allow_html=True)
        if zones:
            df = pd.DataFrame([
                {
                    "Zone": z["zone_id"],
                    "Count": z["total_count"],
                    "Dominant Debris": z["dominant_debris"],
                    "Risk": z["risk_level"],
                    "Trend": z["trend"],
                }
                for z in zones
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No zones yet. Upload images and run clustering from the 'Hotspot Map' page.")

# ---------------------------------------------------------------
# PAGE: Upload & Detect  (Steps 1-6 from earlier, unchanged logic)
# ---------------------------------------------------------------
elif page == "Upload & Detect":
    st.title("Upload & Detect")

    conf_threshold = st.slider("Confidence threshold", 0.05, 0.95, 0.25, 0.05)
    uploaded_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        save_path = os.path.join(UPLOADS_DIR, uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"Uploaded: {uploaded_file.name}")

        col1, col2 = st.columns(2)
        with col1:
            st.image(save_path, caption="Original Image", use_container_width=True)

        if st.button("Run Detection"):
            try:
                with st.spinner("Running YOLO26n inference..."):
                    result = run_inference(save_path, conf_threshold=conf_threshold)
                st.session_state["last_result"] = result
            except FileNotFoundError as e:
                st.error(f"Model error: {e}")
            except Exception as e:
                st.error(f"Detection failed: {e}")

        if "last_result" in st.session_state and st.session_state["last_result"]["image_name"] == uploaded_file.name:
            result = st.session_state["last_result"]
            with col2:
                st.image(result["annotated_image_path"], caption="Annotated Image", use_container_width=True)

            st.subheader(f"Detected Objects: {len(result['detections'])}")
            if result["detections"]:
                df = pd.DataFrame([
                    {"Debris Type": d["debris_type"], "Confidence": d["confidence"]}
                    for d in result["detections"]
                ])
                st.table(df)
            else:
                st.warning("No objects detected above the current confidence threshold.")

            st.header("Location")
            location_mode = st.radio(
                "Choose how to set the location:",
                ["Enter coordinates", "Search place name"],
                horizontal=True,
            )
            location_name = None
            if location_mode == "Enter coordinates":
                lat_col, lon_col = st.columns(2)
                latitude = lat_col.number_input("Latitude", -90.0, 90.0, 0.0, format="%.6f")
                longitude = lon_col.number_input("Longitude", -180.0, 180.0, 0.0, format="%.6f")
                location_name = st.text_input(
                    "Location name",
                    placeholder="e.g. Marina Beach, Chennai",
                    help="This name is saved in Detection History and used when naming a hotspot zone.",
                ).strip() or "Unnamed location"
            elif location_mode == "Search place name":
                place_name = st.text_input("Place name")
                if st.button("Find location"):
                    try:
                        match = geocode_place(place_name)
                        if match is None:
                            st.session_state.pop("geocoded_location", None)
                            st.session_state.pop("geocoded_query", None)
                            st.error("Place not found. Try a more specific name, such as a city and country.")
                        else:
                            st.session_state["geocoded_location"] = match
                            st.session_state["geocoded_query"] = place_name.strip()
                    except Exception as e:
                        st.session_state.pop("geocoded_location", None)
                        st.session_state.pop("geocoded_query", None)
                        st.error(f"Location lookup failed: {e}")

                match = st.session_state.get("geocoded_location")
                if match and st.session_state.get("geocoded_query") == place_name.strip():
                    latitude = match["latitude"]
                    longitude = match["longitude"]
                    location_name = match.get("location_name") or match.get("display_name") or place_name.strip()
                    st.success(f"Found: {match['display_name']}")
                    st.caption(f"Coordinates: {latitude:.6f}, {longitude:.6f}")
                else:
                    latitude = 999.0
                    longitude = 999.0
            location_valid = -90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0
            if location_valid:
                st.success(f"Location set: {latitude:.6f}, {longitude:.6f}")

                st.subheader("AI Inspection & Nearby Impact")
                try:
                    nearby_zones = []
                    for zone in crud.get_all_zones():
                        distance_km = 6371.0 * 2 * math.asin(min(1, math.sqrt(
                            math.sin(math.radians(zone["centroid_latitude"] - latitude) / 2) ** 2
                            + math.cos(math.radians(latitude))
                            * math.cos(math.radians(zone["centroid_latitude"]))
                            * math.sin(math.radians(zone["centroid_longitude"] - longitude) / 2) ** 2
                        )))
                        nearby_zones.append({
                            "zone_id": zone["zone_id"],
                            "distance_km": round(distance_km, 3),
                            "count": zone["total_count"],
                            "risk": zone["risk_level"],
                            "dominant_debris": zone["dominant_debris"],
                        })
                    nearby_zones.sort(key=lambda item: item["distance_km"])
                    nearby_zones = nearby_zones[:INSPECTION_CONFIG["max_nearby_zones"]]
                except ConnectionError:
                    nearby_zones = []

                inspection_context = {
                    "image": result["image_name"],
                    "image_path": result["image_path"],
                    "detection_count": len(result["detections"]),
                    "confidence_weighted_count": round(
                        sum(item["confidence"] for item in result["detections"]), 2
                    ),
                    "detected_objects": [
                        {"type": item["debris_type"], "confidence": item["confidence"]}
                        for item in result["detections"]
                    ],
                    "inspection_coordinates": {"latitude": latitude, "longitude": longitude},
                    "nearby_zones": nearby_zones,
                    "nearby_detection_count": sum(zone["count"] for zone in nearby_zones),
                    "nearby_risk_levels": sorted({zone["risk"] for zone in nearby_zones}),
                    "pollution_level": inspection_pollution_level(
                        len(result["detections"]), nearby_zones
                    ),
                }
                st.metric(
                    "Prototype pollution level",
                    inspection_context["pollution_level"],
                )
                question = st.text_input(
                    "Ask about this image and nearby zones",
                    placeholder="How could nearby zones be affected?",
                )
                if st.button("Ask Ollama") and question.strip():
                    with st.spinner("Inspecting detection and zone data..."):
                        chat_result = ask_dashboard_chat(question, inspection_context)
                    st.info(chat_result["answer"])

                if not result["detections"]:
                    st.warning("No detections to save for this image.")
                elif st.button("Save Detections to Database"):
                    try:
                        saved_ids = crud.insert_detections([
                            {
                                "image_name": result["image_name"], "image_path": result["image_path"],
                                "debris_type": d["debris_type"], "confidence": d["confidence"],
                                "latitude": latitude, "longitude": longitude,
                                "location_name": location_name,
                                "detected_at": result["timestamp"],
                            }
                            for d in result["detections"]
                        ])
                        st.success(f"Saved {len(saved_ids)} detection(s) to PostgreSQL.")
                    except ConnectionError as e:
                        st.error(f"Database unavailable: {e}")
                    except Exception as e:
                        st.error(f"Failed to save detections: {e}")
            else:
                st.error("Invalid latitude/longitude.")
    else:
        st.write("No image uploaded yet.")

# ---------------------------------------------------------------
# PAGE: Hotspot Map
# ---------------------------------------------------------------
elif page == "Hotspot Map":
    st.title("Hotspot Map")

    eps_km = st.number_input("DBSCAN eps (km)", value=CLUSTERING_CONFIG["eps_km"], step=0.1)
    min_samples = st.number_input("DBSCAN min_samples", value=CLUSTERING_CONFIG["min_samples"], step=1, min_value=1)

    if st.button("Run Clustering & Generate Zones"):
        try:
            points = crud.get_all_detections()
            if len(points) < min_samples:
                st.warning(f"Only {len(points)} detection(s) in the database — need at least {min_samples} for clustering.")
            else:
                with st.spinner("Running DBSCAN and generating zones..."):
                    result = run_clustering(points, eps_km=eps_km, min_samples=min_samples)
                    zones = generate_zones_from_clusters(result["clusters"])
                st.success(f"Generated/updated {len(zones)} zone(s). {len(result['noise'])} point(s) unclustered.")
        except ConnectionError as e:
            st.error(f"Database unavailable: {e}")

    try:
        zones = crud.get_all_zones()
    except ConnectionError as e:
        st.error(f"Database unavailable: {e}")
        zones = []

    if zones:
        fmap = build_hotspot_map(zones)
        st_folium(fmap, width=1000, height=500)
    else:
        st.info("No zones yet — click 'Run Clustering & Generate Zones' after saving some detections.")

# ---------------------------------------------------------------
# PAGE: Zone Analysis
# ---------------------------------------------------------------
elif page == "Zone Analysis":
    st.title("Zone Analysis")

    try:
        zones = crud.get_all_zones()
    except ConnectionError as e:
        st.error(f"Database unavailable: {e}")
        zones = []

    if not zones:
        st.info("No zones available yet.")
    else:
        zone_ids = [z["zone_id"] for z in zones]
        selected_id = st.selectbox("Select a zone", zone_ids)
        zone = next(z for z in zones if z["zone_id"] == selected_id)

        col1, col2, col3 = st.columns(3)
        col1.metric("Current Count", zone["total_count"])
        with col2:
            st.markdown("**Risk Level**")
            st.markdown(badge(zone["risk_level"], {"LOW": "low", "MEDIUM": "medium", "HIGH": "high"}.get(zone["risk_level"], "medium")), unsafe_allow_html=True)
        col3.metric("Trend", zone["trend"])

        st.subheader("Debris Breakdown")
        if zone["class_breakdown"]:
            df = pd.DataFrame(list(zone["class_breakdown"].items()), columns=["Debris Type", "Count"])
            st.bar_chart(df.set_index("Debris Type"))

        st.subheader("Ollama Analysis")
        if zone["recommendation"]:
            st.write(f"**Cleanup recommendation:** {zone['recommendation']}")
        else:
            st.info("No Ollama analysis generated yet for this zone.")

        st.subheader("Historical Trend")
        history = crud.get_zone_history(selected_id)
        if history:
            df_hist = zone_history_dataframe(history)
            st.line_chart(df_hist)
        else:
            st.info("No history recorded yet for this zone.")

# ---------------------------------------------------------------
# PAGE: Detection History
# ---------------------------------------------------------------
elif page == "Detection History":
    st.title("Detection History")

    try:
        detections = crud.get_all_detections()
    except ConnectionError as e:
        st.error(f"Database unavailable: {e}")
        detections = []

    if detections:
        df = pd.DataFrame(detections)
        if "location_name" not in df:
            df["location_name"] = df.apply(
                lambda row: f"{row['latitude']},{row['longitude']}", axis=1
            )
        df["zone_id"] = df["zone_id"].fillna(df["location_name"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No detections stored yet.")

# ---------------------------------------------------------------
# PAGE: About / Methodology
# ---------------------------------------------------------------
elif page == "About / Methodology":
    st.title("About / Methodology")
    st.markdown(f"""
**What this system does:**
- Runs a trained YOLO26n model on user-uploaded images to detect floating/ocean debris.
- Associates each detection with a latitude/longitude entered manually or chosen from
  labeled demo/simulated locations.
- Stores every detection in PostgreSQL.
- Groups nearby detections into hotspot zones using DBSCAN with a haversine
  (true geographic) distance metric.
- Calculates zone statistics (counts, debris breakdown, trend vs. history) entirely
  in Python/SQL — never estimated by an LLM.
- Applies a transparent, configurable rule-based risk classification
  (see `config.RISK_THRESHOLDS`) — **not a scientific environmental risk model.**
- Sends only the already-calculated zone summary to a locally running Ollama model,
  which interprets (not calculates) the numbers into plain-language notes.

**What this system does NOT do:**
- It does not acquire real-time GPS data from physical hardware.
- It does not perform real-world autonomous cleanup.
- It does not provide a scientifically validated environmental risk prediction.
- It does not monitor an actual ocean/beach site live.

This interface is designed so manually/demo-entered coordinates can later be
replaced by a GPS-enabled hardware platform without changing the rest of the pipeline.
""")