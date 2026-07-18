from sympy import Indexed, Symbol
import sympy
from typing import Set

def custom_symbol(index: Indexed) -> set[Symbol]:
    return
index.free_symbols

# --- test ---

a = Indexed("A", 0)
output = custom_symbol(a)

import warnings
from sympy.utilities.exceptions import SymPyDeprecationWarning

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always", SymPyDeprecationWarning)
    
    A = Symbol('A')
    A0 = Indexed('A', 0)
    expect = {A, A0}
    assert output == expect
    assert not any(isinstance(warn.message, SymPyDeprecationWarning) for warn in w), "Test Failed: Deprecation warning was triggered!"
