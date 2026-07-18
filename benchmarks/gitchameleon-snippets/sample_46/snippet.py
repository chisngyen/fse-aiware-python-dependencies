from sklearn.cross_decomposition import CCA
import numpy as np
def get_coef_shape(cca_model: CCA, X: np.ndarray, Y: np.ndarray) -> tuple:
    cca_model.fit(X, Y)
    return
cca_model.coef_.shape

# --- test ---
X = np.random.rand(100, 10)
Y = np.random.rand(100, 5)
cca_model = CCA()
correct_shape=(Y.shape[1], X.shape[1])
assert get_coef_shape(cca_model, X, Y) == correct_shape
