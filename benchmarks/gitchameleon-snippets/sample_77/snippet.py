import numpy as np

def custom_product(arr:np.ndarray) -> np.ndarray:
    return
np.product(arr)

# --- test ---


def test_custom_product():
    arr = np.array([1, 2, 3, 4])
    result = custom_product(arr)
    expected = 24
    assert result == expected

test_custom_product()
