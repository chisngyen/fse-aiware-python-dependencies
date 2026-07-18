import warnings
from scipy.linalg import det
import numpy as np
warnings.filterwarnings('error')

def check_invertibility(matrices: np.ndarray) -> np.bool_:

    return np.all(det(matrices))

# --- test ---

matrices = np.array([
    [[1, 2],
     [3, 4]],
    
    [[0, 1],
     [1, 0]],
    
    [[2, 0],
     [0, 2]]
])
assertion_value = check_invertibility(matrices)
assert assertion_value
matrices = np.array([
    [[1, 2],
     [3, 4]],
    
    [[0, 1],
     [1, 0]],
    
    [[2, 0],
     [0, 2]],

    [[0, 0],
     [0, 0]]
])
assertion_value = not check_invertibility(matrices)
assert assertion_value
