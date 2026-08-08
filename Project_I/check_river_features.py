from datetime import datetime

from data_fetching_and_db.config.config_ import DB_CONFIG
from data_fetching_and_db.services.db_service import AQIDatabase

from src.features.feature_master_pipeline import prepare_model_input

from model.river_model_service import RiverAQIPredictor


def main():

    # ---------------------------------------------------------
    # 1. Database
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

    print("=" * 70)
    print("RIVER FEATURE COMPATIBILITY CHECK")
    print("=" * 70)

    print(
        f"Database rows retrieved: {len(history_df)}"
    )

    # ---------------------------------------------------------
    # 2. Load River model
    # ---------------------------------------------------------

    river = RiverAQIPredictor()

    training_features = river.get_feature_columns()

    print(
        f"River expects: {len(training_features)} features"
    )

    # ---------------------------------------------------------
    # 3. Generate live features
    # ---------------------------------------------------------

    X = prepare_model_input(
        dt=datetime.now(),
        history_df=history_df,
        training_columns=training_features,
    )

    live_features = list(X.columns)

    print(
        f"Live pipeline produced: {len(live_features)} features"
    )

    # ---------------------------------------------------------
    # 4. Compare feature names
    # ---------------------------------------------------------

    training_set = set(training_features)
    live_set = set(live_features)

    missing = training_set - live_set
    extra = live_set - training_set

    print("\n" + "-" * 70)
    print("FEATURE NAME COMPARISON")
    print("-" * 70)

    if not missing:
        print("✅ No River training features are missing.")

    else:
        print(
            f"❌ Missing features: {len(missing)}"
        )

        for feature in sorted(missing):
            print("   ", feature)

    if not extra:
        print("✅ No unexpected live features.")

    else:
        print(
            f"⚠️ Extra live features: {len(extra)}"
        )

        for feature in sorted(extra):
            print("   ", feature)

    # ---------------------------------------------------------
    # 5. Check ordering
    # ---------------------------------------------------------

    same_order = (
        training_features == live_features
    )

    print("\n" + "-" * 70)
    print("FEATURE ORDER")
    print("-" * 70)

    if same_order:
        print(
            "✅ Feature order exactly matches training."
        )

    else:
        print(
            "⚠️ Feature order differs."
        )

        print(
            "River service will reindex the features, "
            "so order alone is not necessarily a problem."
        )

    # ---------------------------------------------------------
    # 6. Check missing values
    # ---------------------------------------------------------

    print("\n" + "-" * 70)
    print("VALUE CHECK")
    print("-" * 70)

    null_columns = X.columns[
        X.isnull().any()
    ].tolist()

    if not null_columns:
        print(
            "✅ No missing values in the generated feature vector."
        )

    else:
        print(
            f"❌ Missing values found in "
            f"{len(null_columns)} columns:"
        )

        for column in null_columns:
            print("   ", column)

    # ---------------------------------------------------------
    # 7. Display feature names
    # ---------------------------------------------------------

    print("\n" + "-" * 70)
    print("RIVER TRAINING FEATURES")
    print("-" * 70)

    for i, feature in enumerate(
        training_features,
        start=1
    ):
        print(
            f"{i:02d}. {feature}"
        )

    print("\n" + "=" * 70)
    print("CHECK COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()