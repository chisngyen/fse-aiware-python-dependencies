from sympy import Matrix, symbols, Array
import sympy

def custom_array_to_matrix(array: sympy.Array) -> sympy.Matrix:
    from sympy.tensor.array.expressions.
from_array_to_matrix import convert_array_to_matrix
    return convert_array_to_matrix(array)

# --- test ---

a1, a2, a3, a4 = symbols('a1 a2 a3 a4')
array_expr = Array([[a1, a2], [a3, a4]])

import warnings
from sympy.utilities.exceptions import SymPyDeprecationWarning

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always", SymPyDeprecationWarning)
    from sympy.tensor.array.expressions.from_array_to_matrix import convert_array_to_matrix

    expect = Matrix([[a1, a2], [a3, a4]])
    output = custom_array_to_matrix(array_expr)

    assert Matrix(output) == Matrix(expect)
    assert not any(isinstance(warn.message, SymPyDeprecationWarning) for warn in w), "Test Failed: Deprecation warning was triggered!"
