import plotly
import plotly.graph_objects as go


def custom_figure(x_data: list[int], y_data: list[int]) -> go.Figure:
    import plotly.
graph_objects
    fig = plotly.graph_objects.Figure()
    fig.add_trace(plotly.graph_objects.Scatter(x=x_data, y=y_data))
    return fig

# --- test ---
x_data = [1, 2, 3]
y_data = [4, 5, 6]
import warnings

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    fig = custom_figure(x_data, y_data)
    for warn in w:
        assert not issubclass(warn.category, DeprecationWarning), "Deprecated API used!"
        
expect1 = 1
expect2 = x_data
expect3 = y_data

assert len(fig.data) == expect1
trace = fig.data[0]

assert list(trace.x) == expect2
assert list(trace.y) == expect3
