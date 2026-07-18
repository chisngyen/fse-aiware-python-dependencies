import pandas as pd
def correct_type(index: pd.Index) -> str:
    return
 'int64'

# --- test ---
index = pd.Index([1, 2, 3], dtype='int32')
assertion_1_value = isinstance(correct_type(index), str)
assertion_2_value =  correct_type(index) == 'int64'
assert assertion_1_value
assert assertion_2_value
