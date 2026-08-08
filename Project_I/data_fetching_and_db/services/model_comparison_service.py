# data_fetching_and_db/services/model_comparison_service.py

"""
Model Comparison service.

Compares:

    XGBoost prediction made yesterday
    River prediction made yesterday
    Today's actual observation

The comparison is always based on TODAY'S DATE.

Example:

    Aug 7:
        XGBoost -> predicts Aug 8
        River   -> predicts Aug 8

    Aug 8:
        Actual Aug 8 arrives

    Comparison:
        XGBoost prediction for Aug 8
        River prediction for Aug 8
        Actual Aug 8

This module does NOT run predictions.
It only reads already-generated data.
"""

from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd

from .db_service import get_connection

from .river_prediction_csv_service import (
    CSV_PATH as RIVER_CSV_PATH,
    initialize_csv as initialize_river_csv,
)


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DAILY_DATA_CSV =  Path("data/daily_data.csv")


# ============================================================
# TABLE ROW DEFINITIONS
# ============================================================

PARAMETER_ROWS = [
    {
        "key": "aqi",
        "label": "AQI",
        "river_col": "river_aqi",
    },
    {
        "key": "pm25",
        "label": "PM2.5",
        "river_col": "river_pm25",
    },
    {
        "key": "pm10",
        "label": "PM10",
        "river_col": "river_pm10",
    },
    {
        "key": "temp",
        "label": "Temperature",
        "river_col": "river_temp",
    },
]


# ============================================================
# HELPER: SAFE ROUNDING
# ============================================================

def _safe_round(value) -> Optional[float]:
    """
    Safely convert a value to float and round to 2 decimals.
    Returns None when the value is missing or invalid.
    """

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


# ============================================================
# RIVER PREDICTION FOR A SPECIFIC DATE
# ============================================================

def _get_river_prediction_for_date(
    target_date_str: str,
) -> Optional[dict]:
    """
    Get the River prediction whose target_date matches
    target_date_str.

    IMPORTANT:
    We do NOT select the latest River prediction.

    Example:

        2026-08-07 -> predicts 2026-08-08
        2026-08-08 -> predicts 2026-08-09

    On 2026-08-08, this function selects:

        target_date = 2026-08-08

    because that is the prediction being evaluated today.
    """

    initialize_river_csv()

    if not RIVER_CSV_PATH.exists():
        return None

    try:
        df = pd.read_csv(RIVER_CSV_PATH)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return None

    if df.empty:
        return None

    if "target_date" not in df.columns:
        return None

    # Normalize dates before comparison.
    df["target_date"] = (
        pd.to_datetime(
            df["target_date"],
            format="mixed",
            errors="coerce",
        )
        .dt.strftime("%Y-%m-%d")
    )

    matches = df[df["target_date"] == target_date_str]

    if matches.empty:
        return None

    # If somehow multiple records exist for the same target date,
    # use the most recently generated prediction.
    if "prediction_date" in matches.columns:
        matches = matches.copy()

        matches["prediction_date"] = (
            pd.to_datetime(
                matches["prediction_date"],
                format="mixed",
                errors="coerce",
            )
        )

        matches = matches.sort_values(
            "prediction_date"
        )

    return matches.iloc[-1].to_dict()


# ============================================================
# XGBOOST PREDICTION
# ============================================================

def _get_xgboost_prediction_for_date(
    target_date_str: str,
) -> dict:
    """
    Fetch the XGBoost prediction already stored in PostgreSQL.

    This function DOES NOT run XGBoost.
    """

    conn = get_connection()

    try:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    predicted_pm25,
                    predicted_pm10,
                    predicted_aqi,
                    predicted_temperature
                FROM predicted_values
                WHERE prediction_date = %s
                """,
                (target_date_str,),
            )

            row = cur.fetchone()

            if not row:
                return {}

            return {
                "pm25": _safe_round(row[0]),
                "pm10": _safe_round(row[1]),
                "aqi": _safe_round(row[2]),
                "temp": _safe_round(row[3]),
            }

    finally:
        conn.close()


# ============================================================
# ACTUAL OBSERVATION
# ============================================================

def _get_actual_for_date(
    target_date_str: str,
) -> Optional[dict]:
    """
    Get the actual observation for target_date_str
    from daily_data.csv.

    Returns None if today's observation is not available.
    """

    if not DAILY_DATA_CSV.exists():
        return None

    try:
        df = pd.read_csv(DAILY_DATA_CSV)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return None

    if df.empty or "datetime" not in df.columns:
        return None

    # Normalize datetime to YYYY-MM-DD.
    df["datetime"] = (
        pd.to_datetime(
            df["datetime"],
            format="mixed",
            errors="coerce",
        )
        .dt.strftime("%Y-%m-%d")
    )

    matches = df[df["datetime"] == target_date_str]

    if matches.empty:
        return None

    row = matches.iloc[-1]

    return {
        "pm25": _safe_round(row.get("pm25")),
        "pm10": _safe_round(row.get("pm10")),
        "aqi": _safe_round(row.get("aqi")),
        "temp": _safe_round(row.get("temp")),
    }


# ============================================================
# MAIN COMPARISON FUNCTION
# ============================================================

def get_model_comparison() -> dict:
    """
    Compare today's actual observation with:

        - XGBoost prediction for today
        - River prediction for today, if available
        - Today's actual value

    River is optional. If River has not produced a prediction
    for today, its column will show None / "Not recorded".

    XGBoost and actual data should still be displayed.
    """

    # --------------------------------------------------------
    # 1. TODAY
    # --------------------------------------------------------

    today_str = str(date.today())

    # --------------------------------------------------------
    # 2. RIVER PREDICTION FOR TODAY
    #
    # This may legitimately be None.
    # DO NOT return early if it is missing.
    # --------------------------------------------------------

    river_row = _get_river_prediction_for_date(
        today_str
    )

    # --------------------------------------------------------
    # 3. XGBOOST PREDICTION FOR TODAY
    # --------------------------------------------------------

    xgboost_values = _get_xgboost_prediction_for_date(
        today_str
    )

    # --------------------------------------------------------
    # 4. TODAY'S ACTUAL
    # --------------------------------------------------------

    actual_values = _get_actual_for_date(
        today_str
    )

    # --------------------------------------------------------
    # 5. BUILD COMPARISON ROWS
    # --------------------------------------------------------

    rows = []

    for parameter in PARAMETER_ROWS:

        # XGBoost
        xgboost_value = xgboost_values.get(
            parameter["key"]
        )

        # River
        river_value = None

        if river_row is not None:
            river_value = _safe_round(
                river_row.get(
                    parameter["river_col"]
                )
            )

        # Actual
        actual_value = None

        if actual_values is not None:
            actual_value = actual_values.get(
                parameter["key"]
            )

        rows.append(
            {
                "parameter": parameter["label"],
                "xgboost": xgboost_value,
                "river": river_value,
                "actual": actual_value,
            }
        )

    # --------------------------------------------------------
    # 6. RETURN TABLE
    # --------------------------------------------------------

    return {
        "target_date": today_str,
        "data": rows,
    }