import joblib


MODEL_PATH = "model/multioutput_xgboost_aqi_forecaster.pkl"


class AQIPredictor:

    def __init__(self):

        bundle = joblib.load(MODEL_PATH)

        self.model = bundle["model"]
        self.feature_cols = bundle["feature_cols"]

    def predict(self, X):

        X = X.reindex(
            columns=self.feature_cols,
            fill_value=0
        )

        return self.model.predict(X)