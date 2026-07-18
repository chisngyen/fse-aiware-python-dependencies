import sympy

def custom_jacobi_symbols(a: int, n: int) -> int:
    return
sympy.jacobi_symbol(a, n)

# --- test ---

import warnings
from sympy.utilities.exceptions import SymPyDeprecationWarning

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always", SymPyDeprecationWarning)
    
    expect = -1
    output = custom_jacobi_symbols(1001, 9907)
    assert output == expect

    assert not any(isinstance(warn.message, SymPyDeprecationWarning) for warn in w), "Test Failed: Deprecation warning was triggered!"
