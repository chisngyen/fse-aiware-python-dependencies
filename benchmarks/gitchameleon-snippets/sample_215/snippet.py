import numpy as np


def custom_iqr(data: np.ndarray) -> float:
    from
scipy.stats import iqr
    return iqr(data)

# --- test ---
data_array = np.array([1, 2, 3, 4, 5])

computed_iqr = custom_iqr(data_array)
expect = 2
assert computed_iqr == expect
