from typing import Tuple
from sympy import laplace_transform, symbols, eye
import sympy

def custom_laplace_transform(t: sympy.Symbol, z: sympy.Symbol) -> Tuple[sympy.Matrix, sympy.Expr, bool]:
    return
laplace_transform(eye(2), t, z, legacy_matrix=False)

# --- test ---
t, z = symbols('t z')
from sympy import Matrix
output = custom_laplace_transform(t,z)
expected = (Matrix([
    [1/z,   0],
    [  0, 1/z]
]), 0, True)
assert output == expected
