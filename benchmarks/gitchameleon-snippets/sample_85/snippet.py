import lightgbm as lgb
import numpy as np
import ctypes

def convert_cint32_array_to_numpy(c_pointer: ctypes.POINTER, length: int) -> np.ndarray:
    """
    Convert a ctypes pointer to a numpy array.
    
    Args:
        c_pointer (c_array_type): A ctypes pointer to an array of integers.
        length (int): The length of the array.
        
    Returns:
        np.ndarray: A numpy array containing the elements of the ctypes array.
    """
    return lgb
.basic.cint32_array_to_numpy(c_pointer, length)

# --- test ---
c_array_type = ctypes.POINTER(ctypes.c_int32)
c_array = (ctypes.c_int32 * 5)(1, 2, 3, 4, 5)
c_pointer = ctypes.cast(c_array, c_array_type)
length = 5
np_array = convert_cint32_array_to_numpy(c_pointer, length)
assertion_1_value = isinstance(np_array, np.ndarray)
assertion_2_value = np_array.shape == (5,)
assertion_3_value = np.array_equal(np_array, np.array([1, 2, 3, 4, 5], dtype=np.int32))
assert assertion_1_value
assert assertion_2_value
assert assertion_3_value
