import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

def custom_violinplot(data: pd.DataFrame) -> Axes:
    return
sns.violinplot(x='x', y='y', data=data, bw_method="scott")

# --- test ---
data = pd.DataFrame({'x': ['A', 'B', 'C'], 'y': [5, 10, 15]})

import warnings

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    
    output = custom_violinplot(data)
    
    warning_messages = [str(warn.message).strip().lower() for warn in w]
    if any("bw" in msg and "deprecated" in msg for msg in warning_messages):
        raise AssertionError("bw parameter should not be used. Use bw_method and bw_adjust instead.")
    
    collections = [c for c in output.collections if isinstance(c, plt.Line2D)]  # Extract violin plot lines
    
    assertion_value = output is not None
    assert assertion_value
