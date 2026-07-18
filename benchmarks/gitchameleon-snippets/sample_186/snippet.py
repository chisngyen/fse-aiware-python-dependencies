from sympy import symbols
from sympy.physics.mechanics import ReferenceFrame
import sympy.physics.vector

def custom_generateInertia(N: sympy.physics.vector.frame.ReferenceFrame, Ixx: sympy.Symbol, Iyy: sympy.Symbol, Izz: sympy.Symbol) -> sympy.physics.vector.dyadic.Dyadic:
    from sympy.
physics.mechanics import inertia
    return inertia(N, Ixx, Iyy, Izz)

# --- test ---

N = ReferenceFrame('N')
Ixx, Iyy, Izz = symbols('Ixx Iyy Izz')
import warnings
from sympy.utilities.exceptions import SymPyDeprecationWarning

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always", SymPyDeprecationWarning)
    from sympy.physics.mechanics import inertia
    expect = Ixx * (N.x | N.x) + Iyy * (N.y | N.y) + Izz * (N.z | N.z)
    assert custom_generateInertia(N, Ixx, Iyy, Izz) == expect
    assert not any(isinstance(warn.message, SymPyDeprecationWarning) for warn in w), "Test Failed: Deprecation warning was triggered!"
