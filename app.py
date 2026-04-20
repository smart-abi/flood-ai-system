import streamlit as st
import pandas as pd
import numpy as np
import json
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import matplotlib.pyplot as plt

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="Flood AI GOD MODE", layout="wide")

st.title("🌊 AI Flood Monitoring System (Live Simulation)")
st.markdown("### Real-time Prediction • Geo Mapping • Smart Alerts")

# -----------------------------
# LOAD MODEL + DATA
# -----------------------------

data = pd.read_csv("combined_flood_data.csv")

# -----------------------------
# MONTH FIX
# -----------------------------
months = [7, 8, 9, 10, 11, 12]
data['Month'] = [months[i % len(months)] for i in range(len(data))]

# -----------------------------
# GEO PROCESS
# -----------------------------
def extract_coords(geo):
    geo_json = json.loads(geo)
    return geo_json["coordinates"]

data["coords"] = data[".geo"].apply(extract_coords)
data["lon"] = data["coords"].apply(lambda x: x[0])
data["lat"] = data["coords"].apply(lambda x: x[1])

# -----------------------------
# SIDEBAR (LIVE CONTROLS)
# -----------------------------
st.sidebar.header("⚙️ Controls")

year = st.sidebar.selectbox("Year", sorted(data["Year"].unique()))
month = st.sidebar.selectbox("Month", sorted(data["Month"].unique()))

# 🔥 LIVE RAINFALL CONTROL
live_rainfall = st.sidebar.slider("🌧️ Live Rainfall Adjustment", 0, 300, 50)

filtered = data[(data["Year"] == year) & (data["Month"] == month)].copy()

# Apply rainfall adjustment
filtered["Rainfall"] = filtered["Rainfall"] + live_rainfall

# -----------------------------
# MODEL PREDICTION
# -----------------------------
# -----------------------------
# AI PREDICTION (SIMULATION MODE)
# -----------------------------
np.random.seed(42)  # for consistent output

filtered["Flood_Prob"] = (
    0.4 * (filtered["Rainfall"] / filtered["Rainfall"].max()) +
    0.3 * filtered["NDWI"] +
    0.2 * (1 / (filtered["Elevation"] + 1)) +
    0.1 * np.random.rand(len(filtered))
)

# Normalize between 0 and 1
filtered["Flood_Prob"] = (
    (filtered["Flood_Prob"] - filtered["Flood_Prob"].min()) /
    (filtered["Flood_Prob"].max() - filtered["Flood_Prob"].min())
)

filtered["Flood"] = (filtered["Flood_Prob"] > 0.5).astype(int)

# -----------------------------
# MAP TYPE
# -----------------------------
map_type = st.radio("Map View", ["Heatmap", "Points"])

# -----------------------------
# CREATE MAP
# -----------------------------
m = folium.Map(
    location=[filtered["lat"].mean(), filtered["lon"].mean()],
    zoom_start=7
)

if map_type == "Heatmap":
    heat_data = [[row["lat"], row["lon"], float(row["Flood_Prob"])]
                 for _, row in filtered.iterrows()]
    HeatMap(heat_data).add_to(m)
else:
    for _, row in filtered.iterrows():
        color = "red" if row["Flood"] == 1 else "green"
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=3,
            color=color,
            fill=True,
            fill_color=color,
        ).add_to(m)

# -----------------------------
# SHOW MAP
# -----------------------------
st.subheader(f"🌍 Flood Map - {month}/{year}")
map_data = st_folium(m, width=900, height=500)

# -----------------------------
# ALERT SYSTEM 🚨
# -----------------------------
high_risk = filtered[filtered["Flood_Prob"] > 0.7]

if len(high_risk) > 0:
    st.error(f"🚨 ALERT: {len(high_risk)} High Flood Risk Zones Detected!")
else:
    st.success("✅ No High Risk Flood Zones")

# -----------------------------
# CLICK ANALYSIS
# -----------------------------
if map_data and map_data["last_clicked"]:

    clicked_lat = map_data["last_clicked"]["lat"]
    clicked_lon = map_data["last_clicked"]["lng"]

    filtered["distance"] = np.sqrt(
        (filtered["lat"] - clicked_lat)**2 +
        (filtered["lon"] - clicked_lon)**2
    )

    nearest = filtered.loc[filtered["distance"].idxmin()]

    st.subheader("📍 Live Location Analysis")

    prob = float(nearest["Flood_Prob"]) * 100

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Flood Probability", f"{prob:.2f}%")

        if prob > 70:
            st.error("🚨 Severe Flood Risk")
        elif prob > 40:
            st.warning("⚠️ Moderate Risk")
        else:
            st.success("✅ Low Risk")

    with col2:
        labels = ["Rainfall", "NDWI", "Elevation"]
        values = [
            nearest["Rainfall"],
            nearest["NDWI"],
            nearest["Elevation"]
        ]

        fig, ax = plt.subplots()
        ax.bar(labels, values)
        st.pyplot(fig)

# -----------------------------
# SUMMARY
# -----------------------------
st.subheader("📊 Dashboard Summary")

flood_count = int(filtered["Flood"].sum())
total = len(filtered)

col1, col2 = st.columns(2)

with col1:
    st.metric("Flood Zones", flood_count)

with col2:
    st.metric("Safe Zones", total - flood_count)
