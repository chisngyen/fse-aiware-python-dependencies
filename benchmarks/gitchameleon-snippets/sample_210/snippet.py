import seaborn as sns
import pandas as pd
from matplotlib.axes import Axes

def custom_violinplot(data: pd.DataFrame) -> Axes:
    return
sns.violinplot(x='x', y='y', data=data, bw_adjust=1.5)

# --- test ---
data = pd.DataFrame({'x': ['A', 'B', 'C'], 'y': [5, 10, 15]})
import warnings

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    
    output = custom_violinplot(data)
    
    warning_messages = [str(warn.message).strip().lower() for warn in w]
    if any("bw" in msg and "deprecated" in msg for msg in warning_messages):
        raise AssertionError("bw parameter should not be used. Use bw_method and bw_adjust instead.")

    for collection in output.collections:
            if hasattr(collection, "get_paths"):
                assertion_value = sns.violinplot.__defaults__[0] == 1.5
                assert assertion_value
