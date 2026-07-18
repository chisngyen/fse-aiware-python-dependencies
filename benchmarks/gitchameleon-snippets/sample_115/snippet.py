from scipy import sparse,linalg
import numpy as np 
def compute_matrix_exponential(A:sparse.lil_matrix)->sparse.lil_matrix:

    return  linalg.expm(A)

# --- test ---

A = sparse.lil_matrix((3, 3))
A[0, 0] = 4
A[1, 1] = 5
A[1, 2] = 6
output = compute_matrix_exponential(A)
expect = np.array([
    [54.59815003,   0.,          0.        ],
    [ 0.,        148.4131591,  176.89579092],
    [ 0.,          0.,           1.        ]
])
assertion_value = np.allclose(output.todense(), expect)
assert assertion_value
