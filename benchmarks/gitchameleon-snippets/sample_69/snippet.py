import numpy as np

def find_common_type(arr1:np.ndarray, arr2:np.ndarray) -> np.dtype:
    return np.
common_type(arr1, arr2)

# --- test ---

array1 = np.array([1, 2, 3])
array2 = np.array([4.0, 5.0, 6.0])
expected_common_type = np.float64
assertion_value = find_common_type(array1, array2) == expected_common_type
assert assertion_value
