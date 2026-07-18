import lightgbm as lgb
import ctypes

def c_str(python_string: str) -> ctypes.c_char_p:
    """
    Convert a Python string to a ctypes c_char_p.
    
    Args:
        python_string (str): The Python string to convert.
        
    Returns:
        ctypes.c_char_p: The converted ctypes c_char_p.
    """
    return
lgb.basic._c_str(python_string)

# --- test ---
python_string = "lightgbm"
c_string = c_str(python_string)
assertion_1_value = isinstance(c_string, ctypes.c_char_p)
assertion_2_value =  c_string.value.decode('utf-8') == python_string
assert assertion_1_value
assert assertion_2_value
