import flask
import werkzeug
from scipy import linalg
import numpy as np

error404 = werkzeug.exceptions.NotFound

def save_exponential(A: np.ndarray, base_path: str, sub_path: str) -> tuple[str, np.ndarray]:
    # Attempt to join the base path and sub path.
    # If the joined path is outside the base path, raise a 404 error.
    # compute the exponential of the batched matrices (m, m) in A (n,m,m)
    # return the save_path and the exponential of the matrices

    joined = flask.safe_join(base_path, sub_path)
    output = np.zeros(A.shape)
    for i in range(A.shape[0]):
        output[i] = linalg.expm(A[i])
    return joined, output

# --- test ---

base_path = '/var/www/myapp'
sub_path = '../secret.txt'
import numpy as np

a = np.random.random((4,3,3))
expected = np.zeros(a.shape)
for i in range(expected.shape[0]):
    expected[i] = linalg.expm(a[i])

try : 
    joined, results = save_exponential(a,base_path, sub_path)
except werkzeug.exceptions.NotFound as e:
    assertion_result = True
else:
    assertion_result = False
assert assertion_result

base_path = '/var/www/myapp'
sub_path = 'secret.txt'

joined, results = save_exponential(a,base_path, sub_path)
assertion_result = joined == '/var/www/myapp/secret.txt' and np.allclose(results, expected)
assert assertion_result
