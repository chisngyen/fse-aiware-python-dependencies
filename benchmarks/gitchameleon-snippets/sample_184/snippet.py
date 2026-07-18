from sympy import *

def custom_function(n: int, k : int) -> int:
    return
divisor_sigma(n, k)

# --- test ---
n = 6
k = 1
output = custom_function(n, k)
import warnings
from sympy.utilities.exceptions import SymPyDeprecationWarning

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always", SymPyDeprecationWarning)
    expect = 12
    assert output == expect
    assert not any(isinstance(warn.message, SymPyDeprecationWarning) for warn in w), "Test Failed: Deprecation warning was triggered!"
