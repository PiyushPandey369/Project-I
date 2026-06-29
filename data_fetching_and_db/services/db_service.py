# services/db_service.py

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
        query = """INSERT INTO predicted_values(datetime,pm25,pm10,aqi,temp)
                   VALUES(
                       %(datetime)s,
                       %(pm25)s,
                       %(pm10)s,
                       %(aqi)s,
                       %(temp)s  
                   )
                   ON CONFLICT (datetime)
                   DO UPDATE SET
                   pm25 = EXCLUDED.pm25,
                   pm10 = EXCLUDED.pm10,
                   aqi = EXCLUDED.aqi,
                   temp = EXCLUDED.temp;
                """
        with conn.cursor() as cur:
            cur.execute(query, data)
        conn.commit()
    finally:
        conn.close()