import numpy as np

def custom_round(arr:np.ndarray) -> np.ndarray:
    return
np.round(arr)

# --- test ---

def test_custom_round():
    arr = np.array([1.5, 2.3, 3.7])
    result = custom_round(arr)
    expected = np.array([2.0, 2.0, 4.0])
    assert np.array_equal(result, expected)

test_custom_round()
