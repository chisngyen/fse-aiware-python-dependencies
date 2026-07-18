from sklearn.impute import SimpleImputer
import numpy as np
def get_imputer(data: np.ndarray) -> SimpleImputer:
    return
SimpleImputer()

# --- test ---
data = np.array([[1, 2, 3], [4, None, 6], [7, 8, None]], dtype=float)
expected_type=SimpleImputer
assert isinstance(get_imputer(data), expected_type)
