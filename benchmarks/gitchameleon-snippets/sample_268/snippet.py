import plotly.graph_objects as go

def custom_fig(x_data: list[int], y_data: list[int], color_set: str) -> go.Figure:
    return
go.Figure(data=go.Scatter(
    x=x_data,
    y=y_data,
    error_y=dict(
        color=color_set
    )
))

# --- test ---
    
import plotly.graph_objects as go

x_data = [1, 2, 3]
y_data = [2, 3, 1]
color_set = 'rgba(0, 0, 0, 0.5)'

output = custom_fig(x_data, y_data, color_set)

expect = "rgba("
assert output.data[0].error_y.color.startswith(expect)
