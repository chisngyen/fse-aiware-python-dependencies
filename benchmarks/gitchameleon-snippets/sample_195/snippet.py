import sympy

def custom_bottom_up(expr: sympy.Expr) -> int:
    return
sympy.bottom_up(expr, lambda x: x.doit())

# --- test ---
expr = sympy.Add(1, sympy.Mul(2, 3))
expect = 7
assert custom_bottom_up(expr) == expect
