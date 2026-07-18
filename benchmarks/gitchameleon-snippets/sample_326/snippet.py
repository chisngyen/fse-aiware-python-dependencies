import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes

def modify(fig: Figure, ax: Axes) -> None:

    ax.set_xticks([], minor=False)
    ax.set_yticks([], minor=False)

# --- test ---
import numpy as np 

fig, ax = plt.subplots()
modify(fig, ax)
assertion_value =  np.array_equal(ax.get_xticks(), np.array([]))
assert assertion_value
assertion_value = (ax.get_xticks() == np.array([])).all()
assert assertion_value
assertion_value =  np.array_equal(ax.get_xticklabels(), np.array([]))
assert assertion_value
assertion_value = (ax.get_xticklabels() == np.array([])).all()
assert assertion_value
