from model_services import AQIPredictor

predictor = AQIPredictor()

print(type(predictor.model))

print(len(predictor.feature_cols))