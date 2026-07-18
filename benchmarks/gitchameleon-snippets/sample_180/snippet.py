from sympy.parsing.mathematica import parse_mathematica
from sympy import Function, Max, Min
import sympy

def custom_parse_mathematica(expr : str) -> int:
    return
parse_mathematica(expr).replace(Function("F"), lambda *x: Max(*x)*Min(*x))

# --- test ---
expr = "F[6,4,4]"
import warnings
from sympy.utilities.exceptions import SymPyDeprecationWarning

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always", SymPyDeprecationWarning)
    expect = 24
    assert custom_parse_mathematica(expr) == expect
    assert not any(isinstance(warn.message, SymPyDeprecationWarning) for warn in w), "Test Failed: Deprecation warning was triggered!"
