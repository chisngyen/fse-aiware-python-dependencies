from matplotlib.colors import *
import numpy as np
cmap = {
    "blue": [[1, 2, 2], [2, 2, 1]],
    "red": [[0, 0, 0], [1, 0, 0]],
    "green": [[0, 0, 0], [1, 0, 0]]
}

cmap_reversed =
LinearSegmentedColormap("custom_cmap", cmap).reversed()

# --- test ---

expected_cmap_reversed = {'blue': [(-1.0, 1, 2), (0.0, 2, 2)], 'red': [(0.0, 0, 0), (1.0, 0, 0)], 'green': [(0.0, 0, 0), (1.0, 0, 0)]}

reversed_cmap_dict = cmap_reversed._segmentdata

assert reversed_cmap_dict == expected_cmap_reversed
