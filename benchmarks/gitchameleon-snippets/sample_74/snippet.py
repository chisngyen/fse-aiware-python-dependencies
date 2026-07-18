import numpy as np

def custom_sometrue(arr:np.ndarray) -> np.ndarray:
    return
np.any(arr)

# --- test ---


def test_custom_sometrue():
    arr = np.array([0, 0, 1, 0])
    result = custom_sometrue(arr)
    expected = True
    assert result == expected

test_custom_sometrue()
