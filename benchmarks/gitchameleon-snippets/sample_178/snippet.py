import sympy.physics.quantum
import sympy
def custom_trace(n: int) -> sympy.physics.quantum.trace.Tr:
    return
sympy.physics.quantum.trace.Tr(n)

# --- test ---
from sympy.physics.quantum.trace import Tr
expect = 2
assert custom_trace(2) == expect
