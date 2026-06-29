# src/features/trend_feature.py

def create_trend_features(df):

    cols = ["pm25", "pm10", "aqi", "temp"]

    for col in cols:

        df[f"{col}_diff1"] = df[col].diff(1)

    return df