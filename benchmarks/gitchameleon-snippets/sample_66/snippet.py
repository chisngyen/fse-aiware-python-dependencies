import numpy as np

def apply_convolution_full(arr1 : np.ndarray, arr2 : np.ndarray) -> np.ndarray:
    return
np.convolve(arr1, arr2, mode="full")

# --- test ---

arr1 = np.array([1, 2, 3])
arr2 = np.array([0, 1, 0.5])
assertion_result = apply_convolution_full(arr1, arr2).all() == False
assert assertion_result
