from data_fetching_and_db.services.prediction_service import (
    predict_next_day
)
from data_fetching_and_db.services.db_service import insert_predicted_data
prediction = predict_next_day()
insert_predicted_data(prediction)
print(prediction)