from nltk.lm.api import accumulate
import operator

def accumulate_functional(iterable, func):
    """
    Accumulate the results of applying a function to an iterable.
    
    Args:
        iterable (iterable): An iterable to accumulate.
        func (function): A function to apply to the elements of the iterable.
        
    Returns:
        list: A list of accumulated results.
    """
    return list(
accumulate(iterable, func))

# --- test ---
iterable = [1, 2, 3, 4, 5]
func = operator.add
result = accumulate_functional(iterable, func)
assertion_value = isinstance(result, list)
assert assertion_value
assertion_value =  result == [1, 3, 6, 10, 15]
assert assertion_value
