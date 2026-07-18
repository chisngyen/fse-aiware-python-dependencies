import sympy

def custom_totient(n: int) -> int:
    return
sympy.totient(n)

# --- test ---
import warnings
from sympy.utilities.exceptions import SymPyDeprecationWarning

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always", SymPyDeprecationWarning)
    
    expect = 8
    output = custom_totient(30)
    assert output == expect

    assert not any(isinstance(warn.message, SymPyDeprecationWarning) for warn in w), "Test Failed: Deprecation warning was triggered!"
