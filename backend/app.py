import streamlit as st
from routes_api import get_routes
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests

# ✅ CONFIG
st.set_page_config(page_title="CarbonIQ", layout="wide")

st.markdown("""
<h1 style='text-align: center; color: #00c853;'>
🌱 CarbonIQ
</h1>
<p style='text-align: center; color: gray;'>
AI-powered Eco Route Recommendation System
</p>
<hr>
""", unsafe_allow_html=True)


# ✅ MODERN UI
st.markdown("""
<style>
body {
    background-color: #0e1117;
    color: white;
}

section.main > div {
    background-color: #0e1117;
}

.stApp {
    background-color: #0e1117;
}

/* Fix dim issue */
iframe {
    background-color: white !important;
}
</style>
""", unsafe_allow_html=True)


# ✅ SESSION
if "routes" not in st.session_state:
    st.session_state.routes = None


# ✅ FUNCTION
@st.cache_data
def get_lat_lon(place):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={place}&format=json"

        res = requests.get(
            url,
            headers={"User-Agent": "carbon-route-ai"},
            timeout=8
        ).json()

        if len(res) > 0:
            return float(res[0]["lat"]), float(res[0]["lon"])

    except:
        return None

    return None


# 🎯 TITLE
st.title("🌱 CarbonIQ - Eco Route Finder")
st.write("Find the lowest carbon emission route between two locations.")

st.markdown("---")

# 🔍 SOURCE
source_query = st.text_input("Search Source")

if "source_options" not in st.session_state:
    st.session_state.source_options = []

if "source_selected" not in st.session_state:
    st.session_state.source_selected = None

col1, col2 = st.columns([3,1])

with col1:
    pass

with col2:
    if st.button("🔍 Search Source"):
        try:
            import time
            time.sleep(1)  # prevent API blocking

            res = requests.get(
                f"https://nominatim.openstreetmap.org/search?q={source_query}&format=json&limit=5",
                headers={
                    "User-Agent": "carbon-route-ai",
                    "Accept-Language": "en"
                },
                timeout=8
            )

            if res.status_code == 200:
                data = res.json()
                st.session_state.source_options = [p["display_name"] for p in data]
            else:
                st.session_state.source_options = []

        except:
            st.warning("⚠️ Network issue. Try again.")
            st.session_state.source_options = []

# dropdown
if st.session_state.source_options:
    st.session_state.source_selected = st.selectbox(
    "Select Source",
    st.session_state.source_options,
    key="src_select"
)

source = st.session_state.source_selected

st.markdown("---")

# 🔍 DESTINATION
dest_query = st.text_input("Search Destination")

if "dest_options" not in st.session_state:
    st.session_state.dest_options = []

if "dest_selected" not in st.session_state:
    st.session_state.dest_selected = None

col3, col4 = st.columns([3,1])

with col3:
    pass

with col4:
    if st.button("🔍 Search Destination"):
        try:
            import time
            time.sleep(1)

            res = requests.get(
                f"https://nominatim.openstreetmap.org/search?q={dest_query}&format=json&limit=5",
                headers={
                    "User-Agent": "carbon-route-ai",
                    "Accept-Language": "en"
                },
                timeout=8
            )

            if res.status_code == 200:
                data = res.json()
                st.session_state.dest_options = [p["display_name"] for p in data]
            else:
                st.session_state.dest_options = []

        except:
            st.warning("⚠️ Network issue. Try again.")
            st.session_state.dest_options = []

# dropdown
if st.session_state.dest_options:
    st.session_state.dest_selected = st.selectbox(
    "Select Destination",
    st.session_state.dest_options,
    key="dest_select"
)

destination = st.session_state.dest_selected

st.markdown("---")

# 🧠 NEW INPUTS
col1, col2 = st.columns(2)

with col1:
    user_type = st.selectbox("👤 User Type", ["Student", "Office Worker", "Family"])

with col2:
    people = st.selectbox("👥 Number of People", [1, 2, 3, 4, 5])

st.markdown("---")

# 🗺 PREVIEW
if source and destination:
    src_coords = get_lat_lon(source)
    dest_coords = get_lat_lon(destination)

    m = folium.Map(location=src_coords if src_coords else [12.97, 77.59], zoom_start=12)

    if src_coords:
        folium.Marker(src_coords, icon=folium.Icon(color="green")).add_to(m)
    if dest_coords:
        folium.Marker(dest_coords, icon=folium.Icon(color="red")).add_to(m)

    st_folium(m, width=900, height=700, key="preview_map")

st.markdown("---")

st.write("DEBUG Source:", st.session_state.get("source_selected"))
st.write("DEBUG Dest:", st.session_state.get("dest_selected"))

# 🚀 BUTTON
if st.button("🚀 Find Eco Routes"):

    # Always fetch latest values from session
    source = st.session_state.get("source_selected")
    destination = st.session_state.get("dest_selected")

    if not source or not destination:
        st.warning("⚠️ Please select source and destination from dropdown")
    else:
        try:
            with st.spinner("Finding best eco routes... 🌍"):
                routes = get_routes(source, destination)

            if not routes:
                st.error("❌ Could not fetch routes. Try again.")
            else:
                st.session_state.routes = routes

        except Exception as e:
            st.error("❌ Network error while fetching routes")

st.markdown("---")

# 📊 USE ROUTES
routes = st.session_state.routes

if not routes:
    st.info("👆 Enter locations and click 'Find Eco Routes' to start")

if routes:

    all_options = []
    shortest_route = min(routes, key=lambda x: x["distance"])

    for route in routes:
        st.markdown(f"""
        <div style="padding:15px;border-radius:12px;background:#1e1e1e;margin-bottom:10px;">
        <b>Route {route['route']}</b><br>
        Distance: {route['distance']:.2f} km<br>
        Time: {route['duration']:.1f} min
        </div>
        """, unsafe_allow_html=True)

        for mode_data in route["modes"]:
            mode = mode_data["mode"]
            co2 = mode_data["co2"]

            icon = "🚗" if mode=="car" else "🏍" if mode=="bike" else "🚌" if mode=="bus" else "🚇"

            st.markdown(f"**{icon} {mode.upper()} → {co2:.2f} kg CO₂**")

            all_options.append({
                "route": route["route"],
                "mode": mode,
                "co2": co2
            })

    best_option = min(all_options, key=lambda x: x["co2"])
    worst = max([m for r in routes for m in r["modes"]], key=lambda x: x["co2"])
    saved = worst["co2"] - best_option["co2"]

    st.markdown(f"""
    <div style="
    padding:20px;
    border-radius:15px;
    background:#003d2b;
    color:white;
    text-align:center;
    margin-bottom:15px;
    ">
    <h3>🌟 Best Eco Route</h3>
    Route {best_option['route']} using {best_option['mode'].upper()}<br>
    CO₂ Saved: {saved:.2f} kg
    </div>
    """, unsafe_allow_html=True)


    # 🧠 SMART AI LOGIC
    def get_ai_suggestions(user_type, people):
        suggestions = []

        if user_type == "Student":
            suggestions.append(("🚇 Metro / 🚌 Bus", "Best for students (low cost + eco)"))

        if user_type == "Office Worker":
            if people == 1:
                suggestions.append(("🏍 Bike", "Fastest in traffic"))
            else:
                suggestions.append(("🚗 Car", "Comfort for office commute"))

        if user_type == "Family":
            suggestions.append(("🚗 Car", "Best for family travel"))

        if people == 1:
            suggestions.append(("🚇 Metro", "Best eco option"))
        elif people >= 3:
            suggestions.append(("🚗 Car", "Better than multiple bikes"))

        return suggestions
    
    st.markdown("---")

    st.markdown("### 🤖 Smart Travel Suggestions")

    suggestions = get_ai_suggestions(user_type, people)
    cols = st.columns(len(suggestions))

    for i, (mode, reason) in enumerate(suggestions):
        with cols[i]:
            st.markdown(f"""
            <div style="padding:15px;border-radius:12px;background:#1f2937;text-align:center;">
            <b>{mode}</b><br><br>
            {reason}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # 📊 CHART BOX
    df = pd.DataFrame(all_options)
    chart_df = df.groupby("mode")["co2"].mean()

    st.markdown("### 📊 CO₂ Comparison")

    st.markdown("""
    <div style="padding:20px;border-radius:15px;background:#111827;">
    """, unsafe_allow_html=True)

    st.bar_chart(chart_df)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # 🗺 MAP
    st.subheader("🗺 Route Map")

    m = folium.Map(location=routes[0]["coordinates"][0], zoom_start=12)

    for route in routes:
        color = "green" if route["route"] == best_option["route"] else "blue"
        folium.PolyLine(route["coordinates"], color=color, weight=6).add_to(m)

    src_coords = get_lat_lon(source)
    dest_coords = get_lat_lon(destination)

    if src_coords:
        folium.Marker(src_coords, icon=folium.Icon(color="green")).add_to(m)
    if dest_coords:
        folium.Marker(dest_coords, icon=folium.Icon(color="red")).add_to(m)

    st_folium(m, width=900, height=700, key="route_map")
    
    st.markdown("---")
    