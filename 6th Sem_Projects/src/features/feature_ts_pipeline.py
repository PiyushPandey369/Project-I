import pandas as pd
from src.features.feature_lag import create_lag_features
from src.features.feature_rolling import create_rolling_features
from src.features.feature_trend import create_trend_features


def create_time_series_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "datetime" not in df.columns:
        raise ValueError("history dataframe must contain a 'date' column")

    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)

    df = create_lag_features(df)
    df = create_rolling_features(df)
    df = create_trend_features(df)

    return df