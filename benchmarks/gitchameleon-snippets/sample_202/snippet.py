import sympy

def custom_npartitions(n: int) -> int:
    return
sympy.functions.combinatorial.numbers.partition(n)

# --- test ---
import warnings
from sympy.utilities.exceptions import SymPyDeprecationWarning

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always", SymPyDeprecationWarning)
    
    expect = 7
    output = custom_npartitions(5)
    assert output == expect

    assert not any(isinstance(warn.message, SymPyDeprecationWarning) for warn in w), "Test Failed: Deprecation warning was triggered!"
