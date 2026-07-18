import sympy
from sympy.matrices.expressions.fourier import DFT

def custom_computeDFT(n: int) -> sympy.ImmutableDenseMatrix:
    return
DFT(n).as_explicit()

# --- test ---

import warnings
from sympy.utilities.exceptions import SymPyDeprecationWarning
from sympy import Matrix, I, Rational

def test_custom_computeDFT():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", SymPyDeprecationWarning)  # Capture all warnings
        output = custom_computeDFT(4)
        expect = Matrix([
            [Rational(1,2), Rational(1,2), Rational(1,2), Rational(1,2)],
            [Rational(1,2), -I/2, -Rational(1,2), I/2],
            [Rational(1,2), -Rational(1,2), Rational(1,2), -Rational(1,2)],
            [Rational(1,2), I/2, -Rational(1,2), -I/2]
        ])

        assert output == expect
        assert not any(isinstance(warn.message, SymPyDeprecationWarning) for warn in w), "Test Failed: Deprecation warning was triggered!"

test_custom_computeDFT()
