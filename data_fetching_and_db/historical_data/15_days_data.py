import requests
import pandas as pd
from datetime import datetime, timedelta

LAT = 27.7054
LON = 85.3146
TIMEZONE = "Asia/Kathmandu"

# Last 15 completed days
end_date = datetime.today().date() - timedelta(days=1)
start_date = end_date - timedelta(days=14)


# =========================
# AQI CALCULATION
# =========================

def calc_pm25_aqi(pm25):
    breakpoints = [
        (0.0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 350.4, 301, 400),
        (350.5, 500.4, 401, 500),
    ]

    for c_low, c_high, i_low, i_high in breakpoints:
        if c_low <= pm25 <= c_high:
            return ((i_high - i_low) /
                    (c_high - c_low)) * (pm25 - c_low) + i_low

    return 500


def calc_pm10_aqi(pm10):
    breakpoints = [
        (0, 54, 0, 50),
        (55, 154, 51, 100),
        (155, 254, 101, 150),
        (255, 354, 151, 200),
        (355, 424, 201, 300),
        (425, 504, 301, 400),
        (505, 604, 401, 500),
    ]

    for c_low, c_high, i_low, i_high in breakpoints:
        if c_low <= pm10 <= c_high:
            return ((i_high - i_low) /
                    (c_high - c_low)) * (pm10 - c_low) + i_low

    return 500


def calculate_aqi(pm25, pm10):
    return max(
        calc_pm25_aqi(pm25),
        calc_pm10_aqi(pm10)
    )


# =========================
# WEATHER DATA
# =========================

weather_url = (
    "https://archive-api.open-meteo.com/v1/archive"
    f"?latitude={LAT}"
    f"&longitude={LON}"
    f"&start_date={start_date}"
    f"&end_date={end_date}"
    f"&timezone={TIMEZONE}"
    "&daily="
    "temperature_2m_mean,"
    "relative_humidity_2m_mean,"
    "pressure_msl_mean,"
    "wind_speed_10m_mean,"
    "wind_direction_10m_dominant,"
    "precipitation_sum,"
    "shortwave_radiation_sum"
)

weather_response = requests.get(weather_url, timeout=60)
weather_response.raise_for_status()

weather_json = weather_response.json()

weather_df = pd.DataFrame({
    "datetime": weather_json["daily"]["time"],
    "temp": weather_json["daily"]["temperature_2m_mean"],
    "humidity": weather_json["daily"]["relative_humidity_2m_mean"],
    "sealevelpressure": weather_json["daily"]["pressure_msl_mean"],
    "windspeed": weather_json["daily"]["wind_speed_10m_mean"],
    "winddir": weather_json["daily"]["wind_direction_10m_dominant"],
    "precipitation": weather_json["daily"]["precipitation_sum"],
    "solarradiation": weather_json["daily"]["shortwave_radiation_sum"],
})

# =========================
# AIR QUALITY DATA
# =========================

aq_url = (
    "https://air-quality-api.open-meteo.com/v1/air-quality"
    f"?latitude={LAT}"
    f"&longitude={LON}"
    f"&start_date={start_date}"
    f"&end_date={end_date}"
    f"&timezone={TIMEZONE}"
    "&hourly=pm2_5,pm10"
)

aq_response = requests.get(aq_url, timeout=60)
aq_response.raise_for_status()

aq_json = aq_response.json()

aq_hourly = pd.DataFrame({
    "time": aq_json["hourly"]["time"],
    "pm25": aq_json["hourly"]["pm2_5"],
    "pm10": aq_json["hourly"]["pm10"],
})

aq_hourly["time"] = pd.to_datetime(aq_hourly["time"])
aq_hourly["datetime"] = aq_hourly["time"].dt.date

aq_daily = (
    aq_hourly
    .groupby("datetime")[["pm25", "pm10"]]
    .mean()
    .reset_index()
)

aq_daily["datetime"] = aq_daily["datetime"].astype(str)

# =========================
# MERGE
# =========================

df = weather_df.merge(aq_daily, on="datetime")

# Visibility unavailable from Open-Meteo
df["visibility"] = None

# Approximation
df["tsp"] = df["pm10"] * 2

# AQI
df["aqi"] = df.apply(
    lambda row: calculate_aqi(
        row["pm25"],
        row["pm10"]
    ),
    axis=1
)

# Round values
numeric_cols = [
    "pm25",
    "pm10",
    "tsp",
    "temp",
    "humidity",
    "windspeed",
    "winddir",
    "sealevelpressure",
    "precipitation",
    "solarradiation",
    "aqi"
]

df[numeric_cols] = df[numeric_cols].round(2)

# =========================
# PRINT
# =========================

pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)

print("\nLAST 15 DAYS DATA\n")
print(df.to_string(index=False))

# Save CSV
# df.to_csv("aqi_daily_last_15_days.csv", index=False)

print("\nCSV saved as: aqi_daily_last_15_days.csv")