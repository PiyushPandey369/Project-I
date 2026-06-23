

from pprint import pprint

from services.weather_service import (
    fetch_current_data
)

from services.db_service import (
    insert_daily_record
)


def main():

    data = fetch_current_data()

    print("\nFetched Data:\n")

    pprint(data)

    insert_daily_record(data)

    print(
        "\nSuccessfully inserted into PostgreSQL."
    )


if __name__ == "__main__":
    main()