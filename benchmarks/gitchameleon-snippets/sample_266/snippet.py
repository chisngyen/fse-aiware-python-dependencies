import plotly.graph_objects as go


def custom_fig(x_data: list[str], y_data: list[int]) -> go.Figure:
    return
go.Figure(data=[go.Bar(x=x_data,y=y_data,orientation="v")])

# --- test ---

x_data = ["A", "B", "C"]
y_data = [10, 15, 7]
output = custom_fig(x_data, y_data)

expect = "v"

assert output.data[0].orientation == expect
