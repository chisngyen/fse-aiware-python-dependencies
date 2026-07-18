from sympy import *
import sympy

def custom_function(eq: sympy.Equality) -> sympy.Expr:
    return
eq.lhs - eq.rhs

# --- test ---
x, y = symbols('x y')
eq = Eq(x, y)
output = custom_function(eq)

import warnings
from sympy.utilities.exceptions import SymPyDeprecationWarning

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always", SymPyDeprecationWarning)
    expect = x - y
    assert output == expect
    assert not any(isinstance(warn.message, SymPyDeprecationWarning) for warn in w), "Test Failed: Deprecation warning was triggered!"
