import numpy as np

def custom_cumproduct(arr:np.ndarray) -> np.ndarray:
    return
np.cumproduct(arr)

# --- test ---

def test_custom_cumproduct():
    arr = np.array([1, 2, 3, 4])
    result = custom_cumproduct(arr)
    expected = np.array([1, 2, 6, 24])
    assert np.array_equal(result, expected)

test_custom_cumproduct()
