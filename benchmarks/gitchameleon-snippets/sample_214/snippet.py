import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.axes import Axes


def custom_set_axis_labels(data: pd.DataFrame) -> Axes:
    ax = sns.scatterplot(x='x', y='y', data=data)
    ax.
set(xlabel="My X Label", ylabel="My Y Label")
    return ax

# --- test ---
data = pd.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]})

ax = custom_set_axis_labels(data)
x_expect = "My X Label"
y_expect = "My Y Label"
assert ax.get_xlabel() == x_expect and ax.get_ylabel() == y_expect, (
    "Axis labels not set correctly using ax.set()."
)
