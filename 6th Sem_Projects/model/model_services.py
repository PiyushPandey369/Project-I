# model/model_service.py

import joblib
from pathlib import Path


MODEL_PATH = (
    Path(__file__).parent /
    "multioutput_xgboost_aqi_forecaster.pkl"
)


class AQIPredictor:

    def __init__(self):

        bundle = joblib.load(MODEL_PATH)

        self.model = bundle["model"]

        self.feature_cols = bundle["feature_cols"]

    def get_feature_columns(self):

        return self.feature_cols

    def predict(self, X):

        X = X.reindex(
            columns=self.feature_cols,
            fill_value=0
        )

        prediction = self.model.predict(X)

        return prediction