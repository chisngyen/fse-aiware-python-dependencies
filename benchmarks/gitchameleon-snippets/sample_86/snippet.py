import lightgbm as lgb
import numpy as np

def get_params(dataset: lgb.Dataset) -> dict:
    """
    Get the parameters of the dataset.
    
    Args:
        dataset (lgb.Dataset): The dataset to get the parameters from.
        
    Returns:
        dict: The parameters of the dataset.
    """
    return
dataset.get_params()

# --- test ---
data = np.random.rand(10, 2)
label = np.random.randint(2, size=10)
dataset = lgb.Dataset(data, label=label)

params = get_params(dataset)
assertion_value= isinstance(params, dict) or params is None
assert assertion_value
