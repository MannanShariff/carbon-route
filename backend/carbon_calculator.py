# emission factors (grams per km)

emission_factors = {
    "car": 192,
    "bike": 103,
    "bus": 105,
    "metro": 41
}

def calculate_co2(distance_km, mode):
    factor = emission_factors.get(mode, 0)
    co2 = distance_km * factor
    return co2 / 1000   