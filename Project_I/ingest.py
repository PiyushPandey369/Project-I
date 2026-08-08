from pprint import pprint

from data_fetching_and_db.services.csv_services import (
    get_latest_record
)

from data_fetching_and_db.services.db_service import (
    insert_daily_record
)


def main():

    data = get_latest_record()

    print("\nLatest CSV Record\n")
    pprint(data)

    insert_daily_record(data)

    print("\nRecord inserted successfully.")

if __name__ == '__main__':
    main()