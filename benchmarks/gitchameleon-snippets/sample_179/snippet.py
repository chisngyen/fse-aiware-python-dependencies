import sympy

def custom_preorder_traversal(expr: sympy.Expr) -> sympy.core.basic.preorder_traversal:
    return
sympy.preorder_traversal(expr)

# --- test ---
expr = sympy.Add(1, sympy.Mul(2, 3))
expect = [7]
assert list(custom_preorder_traversal(expr)) == expect
