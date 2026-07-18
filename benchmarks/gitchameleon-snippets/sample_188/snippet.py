from sympy import symbols, Poly
import sympy

def custom_generatePolyList(poly: sympy.Poly) -> list[int]:
    return
poly.rep.to_list()

# --- test ---

import warnings
from sympy.utilities.exceptions import SymPyDeprecationWarning

x = symbols('x')
p = Poly(x**2 + 2*x + 3)

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always", SymPyDeprecationWarning)
    expect = [1,2,3]
    assert custom_generatePolyList(p) == expect
    assert not any(isinstance(warn.message, SymPyDeprecationWarning) for warn in w), "Test Failed: Deprecation warning was triggered!"
