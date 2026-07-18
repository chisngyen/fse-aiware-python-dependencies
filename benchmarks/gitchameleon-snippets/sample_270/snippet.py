import plotly
import plotly.graph_objects as go

def custom_make_subplots(rows: int, cols: int) -> go.Figure:
    return
plotly.subplots.make_subplots(rows=rows, cols=cols)

# --- test ---
import warnings
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    fig = custom_make_subplots(2, 2)
    for warn in w:
        assert not issubclass(warn.category, DeprecationWarning), "Deprecated API used!"

num_xaxes = sum(1 for key in fig.layout if key.startswith("xaxis"))
num_yaxes = sum(1 for key in fig.layout if key.startswith("yaxis"))
expect1 = 4
expect2 = 4
assert num_xaxes == expect1
assert num_yaxes == expect2
