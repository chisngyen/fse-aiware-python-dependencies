import numpy as np

def custom_alltrue(arr:np.ndarray) -> np.ndarray:
    return
np.alltrue(arr)

# --- test ---


def test_custom_alltrue():
    arr = np.array([1, 1, 1, 1])
    result = custom_alltrue(arr)
    expected = True
    assert result == expected

test_custom_alltrue()
