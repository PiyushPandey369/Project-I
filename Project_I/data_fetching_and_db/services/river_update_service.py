from datetime import date, datetime, timedelta

import pandas as pd

from .db_service import AQIDatabase

from data_fetching_and_db.config.config_ import DB_CONFIG

from src.features.feature_master_pipeline import (
    prepare_model_input
)

from model.river_model_service import (
    RiverAQIPredictor
)


def _get_observation_date(row: pd.Series) -> date:
    """
    Extract the calendar date from the database row.
    Supports either 'datetime' or 'date'.
    """

    if "datetime" in row.index:
        value = row["datetime"]
    elif "date" in row.index:
        value = row["date"]
    else:
        raise ValueError(
            "Database history must contain either "
            "'datetime' or 'date'."
        )

    if pd.isna(value):
        raise ValueError("Observation date is missing.")

    timestamp = pd.to_datetime(value)

    return timestamp.date()


def update_river_from_latest_observation():
    """
    Update River using the newest actual observation.

    IMPORTANT:
    The latest observation is the newly available actual target.

    Its feature vector is reconstructed from the observations
    BEFORE that target date.

    Example:

        Historical data through Aug 7
                    ↓
             features for Aug 7
                    ↓
             actual Aug 8 AQI
                    ↓
             River learns

    This prevents using the actual target itself as an input
    during the update.
    """

    db_url = (
        f"postgresql://"
        f"{DB_CONFIG['user']}:"
        f"{DB_CONFIG['password']}@"
        f"{DB_CONFIG['host']}:"
        f"{DB_CONFIG['port']}/"
        f"{DB_CONFIG['database']}"
    )

    db = AQIDatabase(db_url)

    # 30 days gives enough history for the existing
    # 14-day lag/rolling features plus safety margin.
    history_df = db.get_recent_history(days=30)

    if history_df is None or history_df.empty:
        raise ValueError(
            "No historical data available for River update."
        )

    if len(history_df) < 16:
        raise ValueError(
            "At least 16 observations are required for "
            "a River online update."
        )

    history_df = history_df.copy()

    # Ensure chronological order.
    date_column = (
        "datetime"
        if "datetime" in history_df.columns
        else "date"
    )

    if date_column not in history_df.columns:
        raise ValueError(
            "History must contain 'datetime' or 'date'."
        )

    history_df[date_column] = pd.to_datetime(
        history_df[date_column]
    )

    history_df = history_df.sort_values(
        date_column
    ).reset_index(drop=True)

    # ---------------------------------------------------------
    # Latest row = newly available actual observation
    # ---------------------------------------------------------

    actual_row = history_df.iloc[-1]

    actual_date = _get_observation_date(actual_row)

    # The rows before the actual observation are the information
    # that could have been available when forecasting it.
    feature_history = history_df.iloc[:-1].copy()

    previous_row = feature_history.iloc[-1]

    previous_date = _get_observation_date(previous_row)

    # ---------------------------------------------------------
    # Safety check for calendar continuity.
    # ---------------------------------------------------------

    if actual_date != previous_date + timedelta(days=1):
        print(
            "⚠️ River update skipped:"
            f" no consecutive daily observation between "
            f"{previous_date} and {actual_date}."
        )

        return {
            "updated": False,
            "reason": "calendar_gap",
            "actual_date": actual_date.isoformat(),
            "previous_date": previous_date.isoformat(),
        }

    river = RiverAQIPredictor()

    # ---------------------------------------------------------
    # Construct the feature vector for the target day.
    #
    # We use the previous day's history, not the actual target
    # row, so the actual AQI cannot leak into the features.
    # ---------------------------------------------------------

    X = prepare_model_input(
        dt=previous_date,
        history_df=feature_history,
        training_columns=river.get_feature_columns(),
    )

    result = river.learn_from_actual(
        X=X,
        actual_row=actual_row,
        observation_date=actual_date,
    )

    return result