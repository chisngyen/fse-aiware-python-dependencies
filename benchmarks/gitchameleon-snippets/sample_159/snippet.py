import numpy as np
from scipy.stats import hmean

def count_unique_hmean(data: np.ndarray) -> int:
    # data shape: (n, m)
    # n: number of arrays
    # m: number of elements in each array

    hmean_values = hmean(np.asarray(data), axis=1)
    unique_vals = np.unique(hmean_values, equal_nan=False).shape[0]
    return unique_vals

# --- test ---

data = np.array([
    [1, 2, 3],
    [2, 2, 2],
    [1, np.nan, 3],
    [4, 5, 6],
    [np.nan, 1, np.nan],
    [1, 2, 3]
])
assertion_value = count_unique_hmean(data) == 5
assert assertion_value
