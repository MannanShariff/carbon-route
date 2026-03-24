import requests
import polyline
import numpy as np
import joblib
import os
import streamlit as st
import time


# -----------------------------
# Load ML Model Safely
# -----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "ml_model", "co2_emission_model.pkl")

model = joblib.load(MODEL_PATH)


# -----------------------------
# Convert place name → coordinates (CACHED)
# -----------------------------
@st.cache_data
def get_coordinates(place):

    url = f"https://nominatim.openstreetmap.org/search?q={place}&format=json"

    try:
        time.sleep(1)  # prevent API blocking

        response = requests.get(
            url,
            headers={"User-Agent": "carbon-route-ai"},
            timeout=10
        )

        data = response.json()

        if len(data) == 0:
            return None

        lat = data[0]["lat"]
        lon = data[0]["lon"]

        return f"{lon},{lat}"

    except:
        return None


# -----------------------------
# Get Routes from OSRM (CACHED + SAFE)
# -----------------------------
@st.cache_data
def get_routes(source, destination):

    src = get_coordinates(source)
    dest = get_coordinates(destination)

    if src is None or dest is None:
        return None

    url = f"https://router.project-osrm.org/route/v1/driving/{src};{dest}?alternatives=true&overview=full&geometries=polyline"
    
    print("SRC:", src)
    print("DEST:", dest)
    print("URL:", url)

    # 🔥 SAFE REQUEST WITH RETRY
    data = None

    for _ in range(3):  # more retries
        try:
            response = requests.get(
                url,
                headers={"User-Agent": "carbon-route-ai"},
                timeout=15
            )

            if response.status_code != 200:
                print("❌ OSRM Status:", response.status_code)
                time.sleep(1)
                continue

            data = response.json()

            # check valid response
            if "routes" in data and len(data["routes"]) > 0:
                break
            else:
                print("❌ No routes in response")
                data = None

        except Exception as e:
            print("❌ OSRM Exception:", e)
            time.sleep(1)
            data = None

    if not data or "routes" not in data:
        return None

    routes = data["routes"]

    routes_data = []

    mode_map = {
        "car": 0,
        "bike": 1,
        "bus": 2,
        "metro": 3
    }

    modes = ["car", "bike", "bus", "metro"]

    for i, route in enumerate(routes):

        distance_km = route["distance"] / 1000
        duration_min = route["duration"] / 60

        # traffic estimation
        if duration_min < 10:
            traffic = 1
        elif duration_min < 20:
            traffic = 2
        else:
            traffic = 3

        mode_results = []

        for mode in modes:

            features = np.array([[distance_km, mode_map[mode], traffic]])

            co2 = model.predict(features)[0]

            mode_results.append({
                "mode": mode,
                "co2": co2
            })

        coordinates = polyline.decode(route["geometry"])

        routes_data.append({
            "route": i + 1,
            "distance": distance_km,
            "duration": duration_min,
            "traffic": traffic,
            "modes": mode_results,
            "coordinates": coordinates
        })

    return routes_data