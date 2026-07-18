from sympy import *

def custom_check_carmichael(n: int) -> bool:
    return
is_carmichael(n)

# --- test ---

import warnings
from sympy.utilities.exceptions import SymPyDeprecationWarning

n = 561
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always", SymPyDeprecationWarning)
    from sympy import is_carmichael
    expect = True
    output = custom_check_carmichael(n)
    assert output == expect
    assert not any(isinstance(warn.message, SymPyDeprecationWarning) for warn in w), "Test Failed: Deprecation warning was triggered!"
