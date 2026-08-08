from datetime import datetime

from data_fetching_and_db.config.config_ import DB_CONFIG
from data_fetching_and_db.services.db_service import AQIDatabase

from src.features.feature_master_pipeline import (
    prepare_model_input
)

from model.river_model_service import (
    RiverAQIPredictor
)


def main():

    print("=" * 70)
    print("RIVER PREDICTION TEST")
    print("=" * 70)

    # ---------------------------------------------------------
    # Database
    # ---------------------------------------------------------

    db_url = (
        f"postgresql://"
        f"{DB_CONFIG['user']}:"
        f"{DB_CONFIG['password']}@"
        f"{DB_CONFIG['host']}:"
        f"{DB_CONFIG['port']}/"
        f"{DB_CONFIG['database']}"
    )

    db = AQIDatabase(db_url)

    history_df = db.get_recent_history(days=30)

    print(
        f"History rows: {len(history_df)}"
    )

    # ---------------------------------------------------------
    # River
    # ---------------------------------------------------------

    river = RiverAQIPredictor()

    print(
        "River targets:",
        river.targets
    )

    print(
        "River feature count:",
        len(river.get_feature_columns())
    )

    # ---------------------------------------------------------
    # Feature generation
    # ---------------------------------------------------------

    X = prepare_model_input(
        dt=datetime.now(),
        history_df=history_df,
        training_columns=river.get_feature_columns(),
    )

    print(
        "Generated feature shape:",
        X.shape
    )

    # ---------------------------------------------------------
    # Prediction
    # ---------------------------------------------------------

    predictions = river.predict(X)

    print("\nRiver predictions")
    print("-" * 70)

    for target, value in predictions.items():

        if value is None:
            print(
                f"{target}: None"
            )
        else:
            print(
                f"{target}: {value:.2f}"
            )

    print("\n" + "=" * 70)
    print("RIVER PREDICTION TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()