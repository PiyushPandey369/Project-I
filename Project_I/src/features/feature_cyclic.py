import numpy as np

def cyclic_feature_calc(month, dayofweek, dayofyear):

    return {

        "month_sin":
            np.sin(2 * np.pi * month / 12),

        "month_cos":
            np.cos(2 * np.pi * month / 12),

        "dayofweek_sin":
            np.sin(2 * np.pi * dayofweek / 7),

        "dayofweek_cos":
            np.cos(2 * np.pi * dayofweek / 7),

        "dayofyear_sin":
            np.sin(2 * np.pi * dayofyear / 365),

        "dayofyear_cos":
            np.cos(2 * np.pi * dayofyear / 365)
    }