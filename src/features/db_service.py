# src/database/db_service.py

import pandas as pd
from sqlalchemy import create_engine


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
        
        