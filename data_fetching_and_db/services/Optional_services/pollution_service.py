from datetime import datetime, UTC
import requests

BASE_URL = "https://pollution.gov.np/gss/api/observation"


def fetch_pm():

    today = datetime.now(UTC).strftime("%Y-%m-%d")

    params = {
        "date_from": f"{today}T00:00:00",
        "date_to": f"{today}T23:59:59"
    }

    def get_value(series_id):

        response = requests.get(
            BASE_URL,
            params={
                **params,
                "series_id": series_id
            },
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        if data.get("data"):
            return round(data["data"][-1]["value"], 2)

        return None

    pm10 = get_value(3)
    pm25 = get_value(4)

    return {

        "pm10": pm10,

        "pm25": pm25,

        "tsp": round(pm10 * 2, 2)
        if pm10 is not None
        else None

    }


if __name__ == "__main__":

    print(fetch_pm())