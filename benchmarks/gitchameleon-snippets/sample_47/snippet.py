from sklearn.datasets import make_sparse_coded_signal
def get_signal(n_samples: int, n_features: int, n_components: int, n_nonzero_coefs: int) -> tuple:
    return
make_sparse_coded_signal(n_samples=n_samples, n_features=n_features,n_components=n_components,n_nonzero_coefs=n_nonzero_coefs)

# --- test ---
n_samples=100
n_features=50
n_components=20
n_nonzero_coefs=10
expected_shape_y = (n_features, n_samples)
expected_shape_d = (n_features, n_components)
expected_shape_c = (n_components, n_samples)

y,d,c = get_signal(n_samples, n_features, n_components, n_nonzero_coefs)
assert y.shape == expected_shape_y
assert d.shape == expected_shape_d
assert c.shape == expected_shape_c
