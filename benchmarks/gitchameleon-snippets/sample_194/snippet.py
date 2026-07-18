from sympy import Matrix
import sympy

def custom_function(matrix: sympy.Matrix) -> list[int]:
    return
matrix.todok()

# --- test ---
m = Matrix([[1, 2], [3, 4]])

output = custom_function(m)
output[(0, 0)] = 100

assertion_value = m[0, 0] == 1
assert assertion_value
assertion_value = output[(0, 0)] == 100
assert assertion_value
