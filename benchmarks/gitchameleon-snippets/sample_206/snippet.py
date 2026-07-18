import sympy

def custom_mobius(n: int) -> int:
    return
sympy.mobius(n)

# --- test ---
import warnings
from sympy.utilities.exceptions import SymPyDeprecationWarning

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always", SymPyDeprecationWarning)
    
    expect = -1
    output = custom_mobius(30)
    assert output == expect

    assert not any(isinstance(warn.message, SymPyDeprecationWarning) for warn in w), "Test Failed: Deprecation warning was triggered!"
