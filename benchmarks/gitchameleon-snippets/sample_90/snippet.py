import lightgbm as lgb
import numpy as np

def convert_from_sliced_object(sliced_data: np.ndarray) -> np.ndarray:
    """
    Convert a sliced object to a fixed object.
    
    Args:
        sliced_data (np.ndarray): The sliced object to convert.
        
    Returns:
        np.ndarray: The converted fixed object.
    """
    return lgb
.basic._convert_from_sliced_object(sliced_data)

# --- test ---
data = np.random.rand(100, 10)
sliced_data = data[:, :5]
fixed_data = convert_from_sliced_object(sliced_data)
assert isinstance(fixed_data, np.ndarray)
assert fixed_data.shape == sliced_data.shape
assert np.array_equal(fixed_data, sliced_data)
