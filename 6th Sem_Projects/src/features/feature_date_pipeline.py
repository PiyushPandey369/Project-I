from src.features.feature_calendar import calendar_feature_calc
from src.features.feature_cyclic import cyclic_feature_calc
from src.features.feature_season_encoding import season_encoding


def create_date_features(dt):

    calendar_features = calendar_feature_calc(dt)

    cyclic_features = cyclic_feature_calc(
        calendar_features["month"],
        calendar_features["dayofweek"],
        calendar_features["dayofyear"]
    )

    season_features = season_encoding(
        calendar_features["season"]
    )

    return {

        **calendar_features,
        **cyclic_features,
        **season_features
    }
    
    
