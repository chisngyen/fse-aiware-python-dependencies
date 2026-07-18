from scipy import stats
import numpy as np
def combine_pvalues(A: np.ndarray) -> tuple[float, float]:

    return stats.combine_pvalues(A,'pearson')

# --- test ---

A = np.array([0.01995382, 0.1906752 , 0.71157923, 0.44477942, 0.4535412 ,
       0.67556953, 0.11174941, 0.85494112, 0.33214635, 0.19103228])
output = combine_pvalues(A)
expect = np.array([-12.91643003, 0.11905922])
assertion_value =  np.allclose(np.asarray(output),expect)
assert assertion_value
