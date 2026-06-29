import pandas as pd

CSV_PATH = r"G:/My Drive/AQI_Project/daily_data.csv"


def get_latest_record():

    df = pd.read_csv(CSV_PATH)

    row = df.iloc[-1]

    pm10 = float(row["pm10"])

    return {

        "datetime": str(row["datetime"]),

        "pm25": float(row["pm25"]),

        "pm10": pm10,

        "tsp": round(pm10 * 2, 2),

        "temp": float(row["temp"]),

        "humidity": int(row["humidity"]),

        "windspeed": float(row["windspeed"]),

        "winddir": int(row["winddir"]),

        "sealevelpressure": int(row["sealevelpressure"]),

        "visibility": float(row["visibility"]),

        "precipitation": float(row["precipitation"]),

        "solarradiation": float(row["solarradiation"]),

        "aqi": int(row["aqi"])

    }