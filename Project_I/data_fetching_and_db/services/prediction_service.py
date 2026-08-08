from datetime import datetime, timedelta

from .db_service import AQIDatabase

from data_fetching_and_db.config.config_ import DB_CONFIG

from src.features.feature_master_pipeline import (
    prepare_model_input
)

from model.model_services import (
    AQIPredictor
)

from model.river_model_service import (
    RiverAQIPredictor
)

from .river_prediction_csv_service import save_river_prediction


def _create_db():
    db_url = (
        f"postgresql://"
        f"{DB_CONFIG['user']}:"
        f"{DB_CONFIG['password']}@"
        f"{DB_CONFIG['host']}:"
        f"{DB_CONFIG['port']}/"
        f"{DB_CONFIG['database']}"
    )

    return AQIDatabase(db_url)


def predict_next_day():

    # ---------------------------------------------------------
    # 1. Database
    # ---------------------------------------------------------

    db = _create_db()

    history_df = db.get_recent_history(
        days=30
    )

    if history_df is None or history_df.empty:
        raise ValueError(
            "No historical data available for prediction."
        )

    # ---------------------------------------------------------
    # 2. Load both models
    # ---------------------------------------------------------

    xgb_predictor = AQIPredictor()
    river_predictor = RiverAQIPredictor()

    # ---------------------------------------------------------
    # 3. Create the SAME feature representation
    #
    # The feature engineering pipeline remains unchanged.
    # ---------------------------------------------------------

    X_xgb = prepare_model_input(
        dt=datetime.now(),
        history_df=history_df,
        training_columns=xgb_predictor.get_feature_columns()
    )

    X_river = prepare_model_input(
        dt=datetime.now(),
        history_df=history_df,
        training_columns=river_predictor.get_feature_columns()
    )

    # ---------------------------------------------------------
    # 4. XGBoost prediction
    # ---------------------------------------------------------

    xgb_pred = xgb_predictor.predict(X_xgb)

    # ---------------------------------------------------------
    # 5. River prediction
    # ---------------------------------------------------------

    river_pred = river_predictor.predict(X_river)

    # ---------------------------------------------------------
    # 6. Build result
    # ---------------------------------------------------------

    prediction_date = (
        datetime.now().date()
        + timedelta(days=1)
    )
    save_river_prediction(
    prediction_date=datetime.now().date(),
    target_date=prediction_date,
    prediction={
        "target_pm25": river_pred["target_pm25"],
        "target_pm10": river_pred["target_pm10"],
        "target_aqi": river_pred["target_aqi"],
        "target_temp": river_pred["target_temp"],
    },
)


    return {
        "datetime": prediction_date,

        # Existing XGBoost results
        "pm25": round(float(xgb_pred[0][0]), 2),
        "pm10": round(float(xgb_pred[0][1]), 2),
        "aqi": round(float(xgb_pred[0][2]), 2),
        "temp": round(float(xgb_pred[0][3]), 2),

        # New River results
        "river_pm25": (
            None
            if river_pred["target_pm25"] is None
            else round(float(river_pred["target_pm25"]), 2)
        ),

        "river_pm10": (
            None
            if river_pred["target_pm10"] is None
            else round(float(river_pred["target_pm10"]), 2)
        ),

        "river_aqi": (
            None
            if river_pred["target_aqi"] is None
            else round(float(river_pred["target_aqi"]), 2)
        ),

        "river_temp": (
            None
            if river_pred["target_temp"] is None
            else round(float(river_pred["target_temp"]), 2)
        ),
    }