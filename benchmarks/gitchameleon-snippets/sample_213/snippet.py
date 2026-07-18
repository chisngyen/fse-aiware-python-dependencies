import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.axes import Axes


def custom_boxenplot(data: pd.DataFrame) -> Axes:
    return
sns.boxenplot(x='x', y='y', data=data, width_method='exponential')

# --- test ---

import warnings

data = pd.DataFrame({'x': ['A', 'B', 'C'], 'y': [5, 10, 15]})

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    
    output = custom_boxenplot(data)

    warning_messages = [str(warn.message).strip().lower() for warn in w]
    if any("scale" in msg and "deprecated" in msg for msg in warning_messages):
        raise AssertionError("scale should not be used in boxenplot. Use width_method instead.")

    for artist in output.get_children():
        if hasattr(artist, "get_linestyle") and artist.get_linestyle() in ["-", "--"]:
            break
    else:
        raise AssertionError("Boxen elements are missing, width_method might not be applied.")
