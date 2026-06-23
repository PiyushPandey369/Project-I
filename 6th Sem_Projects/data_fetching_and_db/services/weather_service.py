

from datetime import datetime
import requests

from config.config import (
    OPENWEATHER_API_KEY,
    LAT,
    LON
)

WEATHER_URL = (
    f"https://api.openweathermap.org/data/2.5/weather"
    f"?lat={LAT}"
    f"&lon={LON}"
    f"&units=metric"
    f"&appid={OPENWEATHER_API_KEY}"
)

POLLUTION_URL = (
    f"https://api.openweathermap.org/data/2.5/air_pollution"
    f"?lat={LAT}"
    f"&lon={LON}"
    f"&appid={OPENWEATHER_API_KEY}"
)

SOLAR_URL = (
    f"https://api.open-meteo.com/v1/forecast"
    f"?latitude={LAT}"
    f"&longitude={LON}"
    f"&current=shortwave_radiation"
)


def calculate_us_aqi(pm25):

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

            return round(
                ((i_high - i_low) /
                 (c_high - c_low))
                * (pm25 - c_low)
                + i_low
            )

    return 500


def get_solar_radiation():

    try:
        response = requests.get(SOLAR_URL, timeout=20)

        response.raise_for_status()

        return (
            response.json()
            .get("current", {})
            .get("shortwave_radiation")
        )

    except Exception:
        return None


def fetch_current_data():

    weather_response = requests.get(
        WEATHER_URL,
        timeout=20
    )
    weather_response.raise_for_status()

    pollution_response = requests.get(
        POLLUTION_URL,
        timeout=20
    )
    pollution_response.raise_for_status()

    weather = weather_response.json()
    pollution = pollution_response.json()

    main = weather.get("main", {})
    wind = weather.get("wind", {})

    pollution_record = pollution.get(
        "list",
        [{}]
    )[0]

    components = pollution_record.get(
        "components",
        {}
    )

    pm25 = components.get("pm2_5")
    pm10 = components.get("pm10")

    windspeed = wind.get("speed")

    if windspeed is not None:
        windspeed = round(
            windspeed * 3.6,
            2
        )

    visibility = weather.get("visibility")

    if visibility is not None:
        visibility = round(
            visibility / 1000,
            2
        )

    record = {

        "datetime": datetime.now().date(),

        "pm25": pm25,
        "pm10": pm10,

        "tsp": round(pm10 * 2, 2)
        if pm10 is not None
        else None,

        "temp": main.get("temp"),

        "humidity": main.get("humidity"),

        "windspeed": windspeed,

        "winddir": wind.get("deg"),

        "sealevelpressure": main.get("pressure"),

        "visibility": visibility,

        "precipitation":
            weather.get("rain", {}).get("1h", 0)
            +
            weather.get("snow", {}).get("1h", 0),

        "solarradiation": get_solar_radiation(),

        "aqi":
            calculate_us_aqi(pm25)
            if pm25 is not None
            else None
    }

    return record