from sklearn.metrics.pairwise import manhattan_distances
import numpy as np
def get_pairwise_dist(X: np.ndarray,Y: np.ndarray) -> np.ndarray:
    distances = manhattan_distances(X, Y, sum_over_features=False)
    return
np.sum(distances, axis=1)

# --- test ---
X = np.array([[1, 2], [3, 4], [5, 6]])
Y = np.array([[1, 1], [4, 4]])
expected_result = np.array([1, 5, 5, 1, 9, 3])
assert np.allclose(get_pairwise_dist(X, Y), expected_result, atol=1e-3)
