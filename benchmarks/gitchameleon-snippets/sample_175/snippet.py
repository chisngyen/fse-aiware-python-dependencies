from typing import List
from sympy.stats import Die, sample
import sympy.stats.rv 

def custom_generateRandomSampleDice(dice: sympy.stats.rv.RandomSymbol, X: int) -> List[int]:
    return
[sample(dice) for i in range(X)]

# --- test ---

dice = Die('X', 6)
import warnings
from sympy.utilities.exceptions import SymPyDeprecationWarning

def test_custom_generateRandomSampleDice():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", SymPyDeprecationWarning)  # Capture all warnings
        output = custom_generateRandomSampleDice(dice, 3)
        assert isinstance(output, list), "Test Failed: Output is not a list!"
        assert len(output) == 3, "Test Failed: Output length does not match expected!"
        assert not any(isinstance(warn.message, SymPyDeprecationWarning) for warn in w), "Test Failed: Deprecation warning was triggered!"

test_custom_generateRandomSampleDice()
