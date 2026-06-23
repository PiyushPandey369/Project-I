# src/features/rolling_feature.py

import pandas as pd


def create_rolling_features(df):

    rolling_columns = ["pm25", "pm10", "aqi", "temp"]

    windows = [3, 7, 14]

    for col in rolling_columns:

        shifted = df[col].shift(1)

        for window in windows:

            df[f"{col}_roll{window}"] = (
                shifted
                .rolling(window)
                .mean()
            )

            df[f"{col}_std{window}"] = (
                shifted
                .rolling(window)
                .std()
            )

    return df