from sklearn.datasets import load_digits
from sklearn.utils import Bunch
from sklearn.decomposition import FastICA
def apply_fast_ica(data: Bunch, n_components: int) -> FastICA:
    return
FastICA(n_components=n_components,random_state=0,whiten=True).fit_transform(data)

# --- test ---
data, _ = load_digits(return_X_y=True)
n_components=7
expected_shape = (1797, n_components)
assert apply_fast_ica(data, n_components).shape == expected_shape
