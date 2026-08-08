import sys
import time


# Set stdout/stderr to UTF-8 to prevent unicode encoding
# errors on Windows console.
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')


def run():

    print("=" * 60)
    print("🚀 AQI Prediction System - Pipeline Run")
    print(
        f"Start Time: "
        f"{time.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    print("=" * 60)

    try:

        # -----------------------------------------------------
        # 1. Fetch data
        # -----------------------------------------------------

        print(
            "\nStep 1: Fetching current weather "
            "and air quality data..."
        )

        import fetch_data

        fetch_data.main()

        # -----------------------------------------------------
        # 2. Ingest into PostgreSQL
        # -----------------------------------------------------

        print(
            "\nStep 2: Ingesting latest fetched "
            "record into PostgreSQL database..."
        )

        import ingest

        ingest.main()

        # -----------------------------------------------------
        # 3. Update River
        # -----------------------------------------------------

        print(
            "\nStep 3: Updating River online-learning model..."
        )

        from data_fetching_and_db.services.river_update_service import (
            update_river_from_latest_observation
        )

        river_update = (
            update_river_from_latest_observation()
        )

        if river_update["updated"]:
            print(
                "✅ River model updated successfully."
            )

            print(
                f"   Observation date: "
                f"{river_update['observation_date']}"
            )

            print(
                f"   Targets updated: "
                f"{', '.join(river_update['targets_updated'])}"
            )

        else:
            print(
                "ℹ️ River model was not updated."
            )

            print(
                f"   Reason: "
                f"{river_update.get('reason', 'unknown')}"
            )

        # -----------------------------------------------------
        # 4. Predict next day
        # -----------------------------------------------------

        print(
            "\nStep 4: Running XGBoost + River "
            "and generating tomorrow's predictions..."
        )

        import predict

        predict.main()

        # -----------------------------------------------------
        # Success
        # -----------------------------------------------------

        print("\n" + "=" * 60)
        print(
            "✅ Success: AQI Pipeline run completed successfully!"
        )
        print("=" * 60)

        return True

    except Exception as e:

        print("\n" + "!" * 60)

        print(
            "❌ Error: AQI Pipeline run failed!"
        )

        print(
            f"Details: {e}"
        )

        print("!" * 60)

        import traceback

        traceback.print_exc()

        return False


if __name__ == '__main__':

    success = run()

    sys.exit(
        0 if success else 1
    )