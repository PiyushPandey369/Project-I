from datetime import datetime

def season_calc(month):
    if month in [3, 4, 5]:
        return 'Spring'
    elif month in [6, 7, 8]:
        return 'Monsoon'
    elif month in [9, 10, 11]:
        return 'Autumn'
    else:
        return 'Winter'

def calendar_feature_calc(dt):
    
    features = {}
    
    features['year'] = dt.year
    features['month'] = dt.month
    features['day'] = dt.day
    features["dayofweek"] = dt.weekday()
    features["dayofyear"] = dt.timetuple().tm_yday
    features["is_weekend"] = int(dt.weekday() >= 5)
    features['season'] = season_calc(dt.month)
    
    return features



