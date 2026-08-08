def season_encoding(season):

    features = {

        "season_Autumn": 0,
        "season_Monsoon": 0,
        "season_Spring": 0,
        "season_Winter": 0
    }

    features[f"season_{season}"] = 1

    return features