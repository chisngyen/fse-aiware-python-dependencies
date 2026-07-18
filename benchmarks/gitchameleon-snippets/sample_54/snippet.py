from sklearn.metrics.pairwise import manhattan_distances
import numpy as np
def get_pairwise_dist(X: np.ndarray,Y: np.ndarray) -> np.ndarray:
    return
manhattan_distances(X, Y)

# --- test ---
X = np.array([[1, 2], [3, 4], [5, 6]])
Y = np.array([[1, 1], [4, 4]])
expected_result = np.array([[1, 5], [5, 1], [9, 3]])
assert np.allclose(get_pairwise_dist(X, Y), expected_result, atol=1e-3)
