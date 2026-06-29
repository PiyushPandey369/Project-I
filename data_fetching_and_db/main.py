from services.csv_services import get_latest_record
from services.db_service import insert_daily_record
from pprint import pprint

def main():

    data = get_latest_record()

    print("\nLatest CSV Record:\n")
    pprint(data)

    insert_daily_record(data)

    print("\nSuccessfully inserted into PostgreSQL.")

if __name__ == "__main__":
    main()