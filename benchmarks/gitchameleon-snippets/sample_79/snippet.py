import numpy as np

def custom_anytrue(arr:np.ndarray) -> np.ndarray:
    return
np.sometrue(arr)

# --- test ---

def test_custom_sometrue():
    arr = np.array([0, 0, 1, 0])
    result = custom_anytrue(arr)
    expected = True
    assert result == expected

test_custom_sometrue()
