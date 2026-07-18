from sympy import GF
from sympy.polys.domains.finitefield import FiniteField


def custom_function(K: FiniteField, a: FiniteField) -> int:
    return
K.to_int(a)

# --- test ---
K = GF(6)
a = K(8)
output = custom_function(K, a)

import warnings
from sympy.utilities.exceptions import SymPyDeprecationWarning

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always", SymPyDeprecationWarning)
    expect = 2
    assert output == expect
    assert not any(isinstance(warn.message, SymPyDeprecationWarning) for warn in w), "Test Failed: Deprecation warning was triggered!"
