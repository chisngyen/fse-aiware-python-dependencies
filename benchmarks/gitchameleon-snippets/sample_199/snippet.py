import sympy

def custom_divides(n: int, p: int) -> bool:
    return
n % p == 0

# --- test ---
import warnings
from sympy.utilities.exceptions import SymPyDeprecationWarning

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always", SymPyDeprecationWarning)
    
    expect = True
    output = custom_divides(10,2)

    assert output == expect

    assert not any(isinstance(warn.message, SymPyDeprecationWarning) for warn in w), "Test Failed: Deprecation warning was triggered!"
