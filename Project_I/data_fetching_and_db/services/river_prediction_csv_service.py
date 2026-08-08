# data_fetching_and_db/services/river_prediction_csv_service.py

from pathlib import Path
from datetime import date
import csv


# Project root:
# Project_I/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

CSV_PATH = PROJECT_ROOT / "data" / "river_predicted_values.csv"


COLUMNS = [
    "prediction_date",
    "target_date",
    "river_pm25",
    "river_pm10",
    "river_aqi",
    "river_temp",
]


def initialize_csv():
    """
    Create river_predicted_values.csv if it does not exist.
    """

    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not CSV_PATH.exists():
        with open(
            CSV_PATH,
            mode="w",
            newline="",
            encoding="utf-8",
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=COLUMNS,
            )

            writer.writeheader()


def save_river_prediction(
    prediction_date,
    target_date,
    prediction,
):
    """
    Save one River prediction to CSV.

    Parameters
    ----------
    prediction_date : date
        Date on which the prediction was generated.

    target_date : date
        Date being predicted.

    prediction : dict
        River prediction dictionary containing:
            target_pm25
            target_pm10
            target_aqi
            target_temp
    """

    initialize_csv()

    # Prevent duplicate prediction for the same target date.
    existing_dates = set()

    with open(
        CSV_PATH,
        mode="r",
        newline="",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            existing_dates.add(
                row["target_date"]
            )

    target_date_str = str(target_date)

    if target_date_str in existing_dates:
        print(
            f"⚠️ River prediction already exists "
            f"for {target_date_str}. Skipping."
        )
        return

    row = {
        "prediction_date": str(prediction_date),
        "target_date": target_date_str,

        "river_pm25": round(
            float(prediction["target_pm25"]),
            2,
        ),

        "river_pm10": round(
            float(prediction["target_pm10"]),
            2,
        ),

        "river_aqi": round(
            float(prediction["target_aqi"]),
            2,
        ),

        "river_temp": round(
            float(prediction["target_temp"]),
            2,
        ),
    }

    with open(
        CSV_PATH,
        mode="a",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=COLUMNS,
        )

        writer.writerow(row)

    print(
        f"✅ River prediction saved for {target_date_str}"
    )