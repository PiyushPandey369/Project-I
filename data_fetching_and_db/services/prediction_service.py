from datetime import datetime, timedelta

from src.features.db_service import AQIDatabase

from src.features.feature_master_pipeline import (
    prepare_model_input
)

from model.model_services import (
    AQIPredictor
)


def predict_next_day():

    db = AQIDatabase(
        "postgresql://postgres:root@localhost/aqi_db"
    )

    history_df = db.get_recent_history(
        days=30
    )

    predictor = AQIPredictor()

    X = prepare_model_input(
        dt=datetime.now(),
        history_df=history_df,
        training_columns=predictor.get_feature_columns()
    )
    pred = predictor.predict(X)

    return {
        "datetime": datetime.now().date() + timedelta(days=1),
        "pm25": round(float(pred[0][0]), 2),
        "pm10": round(float(pred[0][1]), 2),
        "aqi": round(float(pred[0][2]), 2),
        "temp": round(float(pred[0][3]), 2)
    }


