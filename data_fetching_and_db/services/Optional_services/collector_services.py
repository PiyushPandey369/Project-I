from datetime import datetime

from services.weather_service import fetch_weather
from services.pollution_service import fetch_pm
from services.aqi_service import fetch_aqi


def fetch_current_data():

    weather = fetch_weather()

    pollution = fetch_pm()

    aqi = fetch_aqi()

    return {

        "datetime": datetime.now().date(),

        **pollution,

        **weather,

        "aqi": aqi

    }


if __name__ == "__main__":

    from pprint import pprint

    pprint(fetch_current_data())