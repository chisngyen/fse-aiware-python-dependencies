from scipy import stats
import numpy as np
def compute_circular_variance(a: np.ndarray)-> float:

    return  1-np.abs(np.mean(np.exp(1j*a)))

# --- test ---

a = np.array([0, 2*np.pi/3, 5*np.pi/3])
output = compute_circular_variance(a)
expect = 0.6666666666666665
assertion_value = np.allclose(output,expect)
assert assertion_value
