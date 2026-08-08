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


def get_dashboard_data_db():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 1. Fetch latest actual record
            cur.execute("""
                SELECT datetime, pm25, pm10, tsp, temp, humidity, windspeed, winddir, sealevelpressure, visibility, precipitation, solarradiation, aqi 
                FROM aqi_daily 
                ORDER BY datetime DESC 
                LIMIT 1
            """)
            latest_actual_row = cur.fetchone()
            latest_actual = None
            if latest_actual_row:
                desc = cur.description
                latest_actual = {desc[i][0]: latest_actual_row[i] for i in range(len(desc))}
                latest_actual['datetime'] = str(latest_actual['datetime'])
            
            # 2. Fetch latest prediction record
            cur.execute("""
                SELECT prediction_date, predicted_pm25, predicted_pm10, predicted_aqi, predicted_temperature 
                FROM predicted_values 
                ORDER BY prediction_date DESC 
                LIMIT 1
            """)
            latest_pred_row = cur.fetchone()
            latest_pred = None
            if latest_pred_row:
                desc = cur.description
                latest_pred = {desc[i][0]: latest_pred_row[i] for i in range(len(desc))}
                latest_pred['prediction_date'] = str(latest_pred['prediction_date'])

            # 3. Fetch historical join (actual vs pred)
            cur.execute("""
                SELECT 
                    d.datetime AS date,
                    d.aqi AS actual_aqi,
                    p.predicted_aqi AS predicted_aqi,
                    d.pm25 AS actual_pm25,
                    p.predicted_pm25 AS predicted_pm25,
                    d.pm10 AS actual_pm10,
                    p.predicted_pm10 AS predicted_pm10,
                    d.temp AS actual_temp,
                    p.predicted_temperature AS predicted_temp
                FROM aqi_daily d
                LEFT JOIN predicted_values p ON d.datetime = p.prediction_date
                ORDER BY d.datetime DESC
                LIMIT 15
            """)
            history_rows = cur.fetchall()
            desc = cur.description
            history = []
            for row in history_rows:
                r_dict = {desc[i][0]: row[i] for i in range(len(desc))}
                r_dict['date'] = str(r_dict['date'])
                history.append(r_dict)
            
            # reverse history so it's chronological
            history.reverse()

            return {
                "latest_actual": latest_actual,
                "latest_prediction": latest_pred,
                "history": history
            }
    finally:
        conn.close()


def get_record_by_date(date_str):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Query actual row
            cur.execute("""
                SELECT datetime, pm25, pm10, tsp, temp, humidity, windspeed, winddir, sealevelpressure, visibility, precipitation, solarradiation, aqi
                FROM aqi_daily
                WHERE datetime = %s
            """, (date_str,))
            actual_row = cur.fetchone()
            actual = None
            if actual_row:
                desc = cur.description
                actual = {desc[i][0]: actual_row[i] for i in range(len(desc))}
                actual['datetime'] = str(actual['datetime'])
            
            # Query predicted row
            cur.execute("""
                SELECT prediction_date, predicted_pm25, predicted_pm10, predicted_aqi, predicted_temperature
                FROM predicted_values
                WHERE prediction_date = %s
            """, (date_str,))
            pred_row = cur.fetchone()
            predicted = None
            if pred_row:
                desc = cur.description
                predicted = {desc[i][0]: pred_row[i] for i in range(len(desc))}
                predicted['prediction_date'] = str(predicted['prediction_date'])
                
            return {
                "date": date_str,
                "actual": actual,
                "predicted": predicted
            }
    finally:
        conn.close()
        