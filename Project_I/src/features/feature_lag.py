# src/features/lag_feature.py

import pandas as pd


def create_lag_features(df):

    lag_columns = ["pm25", "pm10", "aqi", "temp"]

    lag_days = [1, 3, 7, 14]

    for col in lag_columns:

        for lag in lag_days:

            df[f"{col}_lag{lag}"] = df[col].shift(lag)

    return df