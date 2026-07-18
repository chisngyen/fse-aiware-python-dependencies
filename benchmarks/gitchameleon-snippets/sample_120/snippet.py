
from scipy.stats import rv_continuous
def compute_moment(dist : rv_continuous, n: int) -> float:

    return dist.moment(n=n)

# --- test ---

from scipy.stats import norm
import numpy as np
dist = norm(15, 10)
n=5
output = compute_moment(dist, n=n)
expect = 6384375.000000001
assertion_value = np.allclose(output,expect)
assert assertion_value
