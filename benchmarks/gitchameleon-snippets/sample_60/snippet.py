import pandas as pd
import numpy as np
def get_slice(ser: pd.Series, start: int, end: int) -> pd.Series:
    return
ser[start:end]

# --- test ---
ser = pd.Series([1, 2, 3, 4, 5], index=[2, 3, 5, 7, 11])
start,end=2,4
sliced_ser = pd.Series([3, 4], index=[5, 7])
assert sliced_ser.equals(get_slice(ser, start, end)), 'Slicing does not match expected output'
