import numpy as np
from scipy.signal import hilbert

def compute_hilbert_transform(a, b, dtype=np.float64):
    # compute_hilbert_transform should return the Hilbert transform of the
    # a and b arrays stacked vertically, with safe casting and the specified
    # dtype. 
    # raise TypeError if needed

    stacked = np.vstack((a, b), dtype=dtype,
                         casting='safe')
    return hilbert(stacked)

# --- test ---


a = np.array([1.0, 2.0, 3.0], dtype=np.float32)
b = np.array([4.0, 5.0, 6.0], dtype=np.float64)
assertion_value = False
try :
    compute_hilbert_transform(a, b, dtype=np.float32)
except TypeError:
    assertion_value = True
assert assertion_value
b=b.astype(np.float32)
computed = compute_hilbert_transform(a, b, dtype=np.float32)
expected = hilbert(np.vstack([a.astype(np.float64), b.astype(np.float64)])).astype(dtype=np.complex64)
assertion_value = np.allclose(computed, expected) & (computed.dtype == np.complex64)
assert assertion_value
a=a.astype(np.float64)
b=b.astype(np.float64)
computed = compute_hilbert_transform(a, b, dtype=np.float64)
expected = expected.astype(dtype=np.complex128)
assertion_value = np.allclose(computed, expected) & (computed.dtype == np.complex128)
assert assertion_value
