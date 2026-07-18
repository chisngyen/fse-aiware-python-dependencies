from sympy import Matrix
import sympy

def custom_create_matrix(first: sympy.Matrix, second: sympy.Matrix) -> list[int]:
    return
Matrix([first, second])

# --- test ---

first = [1,2]
second =[3,4]
import warnings
from sympy.utilities.exceptions import SymPyDeprecationWarning

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always", SymPyDeprecationWarning)
    
    expected_shape = (2, 2)
    expected_content: list[list[int]] = [[1, 2], [3, 4]]
    output = custom_create_matrix(first, second)

    assert output.shape == expected_shape

    assert output.tolist() == expected_content
    assert not any(isinstance(warn.message, SymPyDeprecationWarning) for warn in w), "Test Failed: Deprecation warning was triggered!"
