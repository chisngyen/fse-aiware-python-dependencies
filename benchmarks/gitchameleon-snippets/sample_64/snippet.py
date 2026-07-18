import pandas as pd
def correct_type(index: pd.Index) -> str:
    return
str(index.dtype)

# --- test ---
index = pd.Index([1, 2, 3], dtype='int32')
assert isinstance(correct_type(index), str)
assert correct_type(index) == "int32"
