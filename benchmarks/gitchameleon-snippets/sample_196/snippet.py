import sympy


def custom_use(expr: sympy.Expr) -> int:
    return
sympy.use(expr, lambda x: x.doit())

# --- test ---
expr = sympy.Add(1, sympy.Mul(2, 3))

expect = 7

assert custom_use(expr) == expect
