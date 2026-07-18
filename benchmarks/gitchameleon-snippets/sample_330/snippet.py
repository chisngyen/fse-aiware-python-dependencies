import matplotlib.pyplot as plt

def use_seaborn() -> None:

    plt.style.use("seaborn-v0_8")

# --- test ---
use_seaborn()

cycle = plt.rcParams['axes.prop_cycle']
from cycler import cycler
a = cycler('color', ['#4C72B0', '#55A868', '#C44E52', '#8172B2', '#CCB974', '#64B5CD'])
assert cycle==a
