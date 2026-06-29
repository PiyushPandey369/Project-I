from dotenv import load_dotenv
import os
load_dotenv()
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
IQAIR_API_KEY = os.getenv("IQAIR_API_KEY")

LAT = 27.7054
LON = 85.3146

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "aqi_db",
    "user": "postgres",
    "password": "root"
}
