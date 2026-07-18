import ctypes
import lightgbm.basic as basic

def create_c_array(values: list, ctype: type) -> ctypes.Array:
    """
    Create a ctypes array from a list of values.
    Args:
        values (list): A list of values to be converted to a ctypes array.
        ctype (type): The ctypes type of the array elements.
    Returns:
        ctypes.Array: A ctypes array containing the values.
    """
    return
basic._c_array(ctype, values)

# --- test ---
CTYPE = ctypes.c_double
VALUES = [0.1, 0.2, 0.3, 0.4, 0.5]
c_array = create_c_array(VALUES, CTYPE)
assertion_1_value = all(isinstance(i, float) for i in c_array)
assertion_2_value = all(c_array[i] == VALUES[i] for i in range(len(VALUES)))

assert assertion_1_value
assert assertion_2_value
