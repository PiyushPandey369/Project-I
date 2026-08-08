from concurrent.futures import ThreadPoolExecutor
import requests

from config.config_ import OPENWEATHER_API_KEY, LAT, LON

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


def celsius_to_fahrenheit(temp):
    if temp is None:
        return None
    return round((temp * 9 / 5) + 32, 2)


def fetch_weather():

    with ThreadPoolExecutor(max_workers=2) as executor:
        weather_future = executor.submit(requests.get, WEATHER_URL, timeout=20)
        solar_future = executor.submit(requests.get, SOLAR_URL, timeout=20)

    weather = weather_future.result().json()
    solar = solar_future.result().json()

    main = weather["main"]
    wind = weather["wind"]

    visibility = weather.get("visibility")
    if visibility is not None:
        visibility = round(visibility / 1000, 2)

    windspeed = wind.get("speed")
    if windspeed is not None:
        windspeed = round(windspeed * 3.6, 2)

    precipitation = 0

    if "rain" in weather:
        precipitation += weather["rain"].get("1h", 0)

    if "snow" in weather:
        precipitation += weather["snow"].get("1h", 0)

    return {

        "temp": celsius_to_fahrenheit(main.get("temp")),

        "humidity": main.get("humidity"),

        "windspeed": windspeed,

        "winddir": wind.get("deg"),

        "sealevelpressure": main.get("pressure"),

        "visibility": visibility,

        "precipitation": precipitation,

        "solarradiation":
            solar.get("current", {}).get("shortwave_radiation")

    }
print(fetch_weather())