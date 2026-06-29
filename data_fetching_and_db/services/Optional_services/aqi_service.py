import requests

from config.config_ import IQAIR_API_KEY, LAT, LON


def fetch_aqi():

    response = requests.get(
        "https://api.airvisual.com/v2/nearest_city",
        params={
            "lat": LAT,
            "lon": LON,
            "key": IQAIR_API_KEY
        },
        timeout=20
    )

    response.raise_for_status()

    return response.json()["data"]["current"]["pollution"]["aqius"]


if __name__ == "__main__":

    print(fetch_aqi())