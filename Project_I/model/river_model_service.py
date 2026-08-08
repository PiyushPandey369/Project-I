import json
import pickle
from pathlib import Path
from datetime import date, datetime

import pandas as pd


MODEL_PATH = Path(__file__).parent / "river_aqi_forecaster.pkl"
STATE_PATH = Path(__file__).parent / "river_update_state.json"


class RiverAQIPredictor:
    """
    Service responsible for:

    1. Loading the trained River models.
    2. Making predictions.
    3. Updating the models with newly available actual observations.
    4. Persisting the updated River model.
    5. Preventing duplicate online updates.

    The River pickle is expected to contain:

        {
            "models": {...},
            "feature_names": [...],
            "targets": [...],
            ...
        }

    One River model exists for each target.
    """

    TARGET_TO_ACTUAL_COLUMN = {
        "target_pm25": "pm25",
        "target_pm10": "pm10",
        "target_aqi": "aqi",
        "target_temp": "temp",
    }

    def __init__(
        self,
        model_path: Path = MODEL_PATH,
        state_path: Path = STATE_PATH,
    ):
        self.model_path = Path(model_path)
        self.state_path = Path(state_path)

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"River model not found: {self.model_path}"
            )

        self._load_model()
        self._load_state()

    # ---------------------------------------------------------
    # MODEL LOADING
    # ---------------------------------------------------------

    def _load_model(self):
        with open(self.model_path, "rb") as file:
            bundle = pickle.load(file)

        if not isinstance(bundle, dict):
            raise ValueError(
                "Invalid River model file. Expected a dictionary bundle."
            )

        required_keys = {
            "models",
            "feature_names",
            "targets",
        }

        missing = required_keys - bundle.keys()

        if missing:
            raise ValueError(
                f"River model bundle is missing keys: {sorted(missing)}"
            )

        self.models = bundle["models"]
        self.feature_names = bundle["feature_names"]
        self.targets = bundle["targets"]

        if not self.models:
            raise ValueError("River model bundle contains no models.")

        if not self.feature_names:
            raise ValueError(
                "River model bundle contains no feature names."
            )

    # ---------------------------------------------------------
    # STATE
    # ---------------------------------------------------------

    def _load_state(self):
        """
        State prevents the same actual observation from being
        learned more than once if the pipeline is accidentally
        executed multiple times on the same day.
        """

        if not self.state_path.exists():
            self.last_updated_date = None
            return

        try:
            with open(self.state_path, "r", encoding="utf-8") as file:
                state = json.load(file)

            value = state.get("last_updated_date")

            if value:
                self.last_updated_date = date.fromisoformat(value)
            else:
                self.last_updated_date = None

        except (json.JSONDecodeError, ValueError):
            self.last_updated_date = None

    def _save_state(self, observation_date: date):
        with open(self.state_path, "w", encoding="utf-8") as file:
            json.dump(
                {
                    "last_updated_date": observation_date.isoformat()
                },
                file,
                indent=2,
            )

        self.last_updated_date = observation_date

    # ---------------------------------------------------------
    # FEATURES
    # ---------------------------------------------------------

    def get_feature_columns(self):
        return self.feature_names

    def prepare_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Make the feature DataFrame match exactly the columns used
        during River training.
        """

        if not isinstance(X, pd.DataFrame):
            raise TypeError("X must be a pandas DataFrame.")

        X = X.copy()

        X = X.reindex(
            columns=self.feature_names,
            fill_value=0,
        )

        # River expects one observation at a time.
        if len(X) != 1:
            raise ValueError(
                "RiverAQIPredictor expects exactly one observation."
            )

        # Convert numpy/pandas scalar values to normal Python values.
        X = X.apply(
            pd.to_numeric,
            errors="coerce"
        )

        if X.isnull().any().any():
            missing_columns = X.columns[
                X.isnull().any()
            ].tolist()

            raise ValueError(
                "River input contains missing/non-numeric values "
                f"in columns: {missing_columns}"
            )

        return X

    def _to_river_dict(self, X: pd.DataFrame):
        """
        Convert one-row DataFrame into River's expected
        {feature_name: value} format.
        """

        row = X.iloc[0]

        return {
            column: float(row[column])
            for column in self.feature_names
        }

    # ---------------------------------------------------------
    # PREDICTION
    # ---------------------------------------------------------

    def predict(self, X: pd.DataFrame):
        """
        Make predictions WITHOUT updating the model.
        """

        X = self.prepare_features(X)
        x_dict = self._to_river_dict(X)

        predictions = {}

        for target in self.targets:
            model = self.models[target]

            prediction = model.predict_one(x_dict)

            if prediction is None:
                predictions[target] = None
            else:
                predictions[target] = float(prediction)

        return predictions

    # ---------------------------------------------------------
    # ONLINE LEARNING
    # ---------------------------------------------------------

    def learn_from_actual(
        self,
        X: pd.DataFrame,
        actual_row: pd.Series,
        observation_date: date,
    ):
        """
        Update all River models using one newly available
        real observation.

        IMPORTANT:
            X must represent the feature vector that was available
            BEFORE the target observation became known.

        The update happens only AFTER prediction.
        """

        if not isinstance(actual_row, pd.Series):
            raise TypeError(
                "actual_row must be a pandas Series."
            )

        if (
            self.last_updated_date is not None
            and observation_date <= self.last_updated_date
        ):
            return {
                "updated": False,
                "reason": (
                    f"Observation {observation_date} was already "
                    f"processed. Last update: "
                    f"{self.last_updated_date}"
                ),
            }

        X = self.prepare_features(X)
        x_dict = self._to_river_dict(X)

        actual_values = {}

        # Validate all targets BEFORE changing any model.
        for target in self.targets:

            if target not in self.TARGET_TO_ACTUAL_COLUMN:
                raise ValueError(
                    f"No actual-data mapping exists for target: {target}"
                )

            actual_column = self.TARGET_TO_ACTUAL_COLUMN[target]

            if actual_column not in actual_row.index:
                raise ValueError(
                    f"Actual observation is missing column: "
                    f"{actual_column}"
                )

            value = actual_row[actual_column]

            if pd.isna(value):
                raise ValueError(
                    f"Actual value for {actual_column} is missing."
                )

            actual_values[target] = float(value)

        # -----------------------------------------------------
        # NOW perform the actual online learning.
        # -----------------------------------------------------

        for target in self.targets:
            self.models[target].learn_one(
                x_dict,
                actual_values[target],
            )

        # Persist the updated models.
        self._save_model()

        # Mark the observation as processed.
        self._save_state(observation_date)

        return {
            "updated": True,
            "observation_date": observation_date.isoformat(),
            "targets_updated": list(actual_values.keys()),
        }

    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------

    def _save_model(self):
        """
        Save the updated River model bundle.
        """

        bundle = {
            "models": self.models,
            "feature_names": self.feature_names,
            "targets": self.targets,
        }

        with open(self.model_path, "wb") as file:
            pickle.dump(bundle, file)

    # ---------------------------------------------------------
    # CONVENIENCE
    # ---------------------------------------------------------

    def predict_aqi(self, X: pd.DataFrame):
        predictions = self.predict(X)

        value = predictions.get("target_aqi")

        if value is None:
            return None

        return float(value)