import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pprint import pprint

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
IQAIR_API_KEY = os.getenv("IQAIR_API_KEY")
LAT = float(os.getenv("LAT", "27.7172"))
LON = float(os.getenv("LON", "85.3240"))

session = requests.Session()
retry = Retry(total=5, backoff_factor=1,
              status_forcelist=[429,500,502,503,504],
              allowed_methods=["GET"])
session.mount("https://", HTTPAdapter(max_retries=retry))

def safe_get(url, **kwargs):
    r = session.get(url, timeout=30, **kwargs)
    r.raise_for_status()
    return r.json()


CSV_PATH = r"data\daily_data.csv"

# Create one reusable session
session = requests.Session()

retry = Retry(
    total=5,
    connect=5,
    read=5,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

adapter = HTTPAdapter(max_retries=retry)

session.mount("https://", adapter)
session.mount("http://", adapter)


def safe_get(url, params=None, timeout=30):
    """
    Reliable GET request with retries and exponential backoff.
    Returns JSON or None.
    """

    for attempt in range(5):

        try:

            response = session.get(
                url,
                params=params,
                timeout=(10, timeout)
            )

            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:

            print(f"Attempt {attempt+1}/5 failed")
            print(e)

            if attempt == 4:
                print("Giving up...")
                return None

            time.sleep(2 ** attempt)

def celsius_to_fahrenheit(temp):
    if temp is None:
        return None
    return round((temp * 9 / 5) + 32, 2)

def fetch_weather():
    WEATHER_URL = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?lat={LAT}"
        f"&lon={LON}"
        "&units=metric"
        f"&appid={OPENWEATHER_API_KEY}"
    )

    SOLAR_URL = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}"
        f"&longitude={LON}"
        "&current=shortwave_radiation"
    )

    # Use safe_get for both API calls
    weather_data = safe_get(WEATHER_URL, timeout=30)
    solar_data = safe_get(SOLAR_URL, timeout=30)

    if weather_data is None or solar_data is None:
        print("Failed to fetch complete weather or solar data.")
        return None

    main = weather_data["main"]
    wind = weather_data["wind"]

    visibility = weather_data.get("visibility")
    if visibility is not None:
        visibility = round(visibility / 1000, 2)

    windspeed = wind.get("speed")
    if windspeed is not None:
        windspeed = round(windspeed * 3.6, 2)

    precipitation = 0

    if "rain" in weather_data:
        precipitation += weather_data["rain"].get("1h", 0)

    if "snow" in weather_data:
        precipitation += weather_data["snow"].get("1h", 0)

    return {
        "temp": celsius_to_fahrenheit(main.get("temp")),
        "humidity": main.get("humidity"),
        "windspeed": windspeed,
        "winddir": wind.get("deg"),
        "sealevelpressure": main.get("pressure"),
        "visibility": visibility,
        "precipitation": precipitation,
        "solarradiation": solar_data.get("current", {}).get("shortwave_radiation")
    }

from datetime import datetime, UTC

BASE_URL = "https://pollution.gov.np/gss/api/observation"

today = datetime.now(UTC).strftime("%Y-%m-%d")


def fetch_pollution():

    def get_pm(series_id):

        data = safe_get(
            BASE_URL,
            {
                "series_id": series_id,
                "date_from": f"{today}T00:00:00",
                "date_to": f"{today}T23:59:59"
            }
        )

        if data is None:
            return None, None

        if data.get("data"):

            latest = data["data"][-1]

            return (
                round(latest["value"], 2),
                latest["datetime"]
            )

        return None, None


    pm10, pm10_time = get_pm(3)
    pm25, pm25_time = get_pm(4)

    return {

        "date": today,

        "pm10": pm10,
        "pm25": pm25,

        "pm10_time": pm10_time,
        "pm25_time": pm25_time

    }


def fetch_aqi():
    IQAIR_URL = (
        "http://api.airvisual.com/v2/nearest_city"
        f"?lat={LAT}"
        f"&lon={LON}"
        f"&key={IQAIR_API_KEY}"
    )

    aqi_data = safe_get(IQAIR_URL, timeout=30)

    if aqi_data is None:
        print("Failed to fetch AQI data.")
        return None

    # Extract the AQI value
    try:
        aqi = aqi_data["data"]["current"]["pollution"]["aqius"]
        return aqi
    except KeyError:
        print("Could not parse AQI from response.")
        return None


def fetch_current_data():

    weather = fetch_weather()

    pollution = fetch_pollution()

    aqi = fetch_aqi()

    return {

        "datetime": datetime.now().date(),

        **pollution,

        **weather,

        "aqi": aqi

    }

def save_to_csv(data):
    # Standardize current date to YYYY-MM-DD format
    current_date = pd.to_datetime(data["datetime"], format='mixed').strftime('%Y-%m-%d')
    # Update data dictionary datetime and date to match standard
    data["datetime"] = current_date
    if "date" in data:
        data["date"] = current_date

    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        # Ensure standard YYYY-MM-DD strings for comparison
        df['datetime'] = pd.to_datetime(df['datetime'], format='mixed').dt.strftime('%Y-%m-%d')
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], format='mixed').dt.strftime('%Y-%m-%d')
        
        # Check if current_date already exists
        if current_date in df['datetime'].values:
            # Update the existing row
            idx = df[df['datetime'] == current_date].index[0]
            for col, val in data.items():
                if col in df.columns:
                    df.at[idx, col] = val
        else:
            # Append new row
            new_row = pd.DataFrame([data])
            df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(CSV_PATH, index=False)
    else:
        df = pd.DataFrame([data])
        df.to_csv(CSV_PATH, index=False)


# Ensure the directory exists before saving
os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)

def main():
    data = fetch_current_data()
    pprint(data)
    save_to_csv(data)
    print("\nSaved successfully.")

if __name__ == '__main__':
    main()

