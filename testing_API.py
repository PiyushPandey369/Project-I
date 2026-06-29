import requests

API_KEY = "1d151320-29f5-4501-b2ba-6d5f39fdcd51"

url = "https://api.airvisual.com/v2/nearest_city"

params = {
    "lat": 27.7172,
    "lon": 85.3240,
    "key": API_KEY
}

response = requests.get(url, params=params)
response.raise_for_status()
data = response.json()["data"]
current = data["current"]
pollution = current["pollution"]
print("AQI:", pollution["aqius"])
