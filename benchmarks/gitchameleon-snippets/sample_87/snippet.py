import numpy as np
import json
from lightgbm.compat import json_default_with_numpy

def dump_json(data: any) -> str:
    """
    Dump data to JSON format.
    
    Args:
        data (any): The data to dump.
        
    Returns:
        str: The JSON representation of the data.
    """
    return json.dumps(data
, default=json_default_with_numpy)

# --- test ---
NUMPY_ARRAY = np.array([1, 2, 3])
json_data = dump_json(NUMPY_ARRAY)
expected = '[1, 2, 3]'
assert json_data == expected
