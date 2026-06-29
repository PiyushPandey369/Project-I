import pandas as pd
from src.features.feature_date_pipeline import create_date_features
from src.features.feature_ts_pipeline import create_time_series_features


def prepare_model_input(dt, history_df: pd.DataFrame, training_columns=None) -> pd.DataFrame:
    """
    dt: today's date/time
    history_df: recent rows from database, including today's row already stored
    training_columns: optional list of columns used during model training
    """

    if len(history_df) < 15:
        raise ValueError("At least 15 rows are required to calculate lag/rolling features")

    # date features from request date
    date_features = create_date_features(dt)

    # time-series features from history
    ts_df = create_time_series_features(history_df)

    latest_row = ts_df.iloc[-1].to_dict()

    # remove DB-only / non-model columns
    latest_row.pop("date", None)

    final_features = {
        **latest_row,
        **date_features,
    }

    X = pd.DataFrame([final_features])

    if training_columns is not None:
        X = X.reindex(columns=training_columns, fill_value=0)

    return X