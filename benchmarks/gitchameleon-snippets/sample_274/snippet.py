import plotly.graph_objs as go

def custom_scatter(custom_color: str) -> go.Figure:
    return
go.Figure(data=[go.Scatter(x=[0],y=[0],marker=go.scatter.Marker(color=custom_color)) ])

# --- test ---
color = 'rgb(255,45,15)'
import warnings

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    fig = custom_scatter(color)
    for warn in w:
        assert not issubclass(warn.category, DeprecationWarning), "Deprecated API used!"

scatter_trace = fig.data[0]
marker_color = scatter_trace.marker.color
expect = color
assert marker_color == expect
