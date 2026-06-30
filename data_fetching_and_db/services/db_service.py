# services/db_service.py
import pandas as pd
from sqlalchemy import create_engine
import psycopg2
from data_fetching_and_db.config.config_ import DB_CONFIG


def get_connection():

    return psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"]
    )


def insert_daily_record(data):

    conn = get_connection()

    try:

        query = """
        INSERT INTO aqi_daily (
            datetime,
            pm25,
            pm10,
            tsp,
            temp,
            humidity,
            windspeed,
            winddir,
            sealevelpressure,
            visibility,
            precipitation,
            solarradiation,
            aqi
        )
        VALUES (
            %(datetime)s,
            %(pm25)s,
            %(pm10)s,
            %(tsp)s,
            %(temp)s,
            %(humidity)s,
            %(windspeed)s,
            %(winddir)s,
            %(sealevelpressure)s,
            %(visibility)s,
            %(precipitation)s,
            %(solarradiation)s,
            %(aqi)s
        )
        ON CONFLICT (datetime)
        DO UPDATE SET
            pm25 = EXCLUDED.pm25,
            pm10 = EXCLUDED.pm10,
            tsp = EXCLUDED.tsp,
            temp = EXCLUDED.temp,
            humidity = EXCLUDED.humidity,
            windspeed = EXCLUDED.windspeed,
            winddir = EXCLUDED.winddir,
            sealevelpressure = EXCLUDED.sealevelpressure,
            visibility = EXCLUDED.visibility,
            precipitation = EXCLUDED.precipitation,
            solarradiation = EXCLUDED.solarradiation,
            aqi = EXCLUDED.aqi;
        """

        with conn.cursor() as cur:
            cur.execute(query, data)

        conn.commit()

    finally:
        conn.close()
        
def insert_predicted_data(data):

    conn = get_connection()

    try:

        query = """
        INSERT INTO predicted_values (
            prediction_date,
            predicted_pm25,
            predicted_pm10,
            predicted_aqi,
            predicted_temperature
        )
        VALUES (
            %(datetime)s,
            %(pm25)s,
            %(pm10)s,
            %(aqi)s,
            %(temp)s
        )
        ON CONFLICT (prediction_date)
        DO UPDATE SET
            predicted_pm25 = EXCLUDED.predicted_pm25,
            predicted_pm10 = EXCLUDED.predicted_pm10,
            predicted_aqi = EXCLUDED.predicted_aqi,
            predicted_temperature = EXCLUDED.predicted_temperature;
        """

        with conn.cursor() as cur:
            cur.execute(query, data)

        conn.commit()

    finally:
        conn.close()
        
class AQIDatabase:

    def __init__(self, db_url):

        self.engine = create_engine(db_url)

    def get_recent_history(self, days=15):

        query = f"""
        SELECT *
        FROM aqi_daily
        ORDER BY datetime DESC
        LIMIT {days}
        """

        df = pd.read_sql(query, self.engine)

        return (
            df
            .sort_values("datetime")
            .reset_index(drop=True)
        )
        