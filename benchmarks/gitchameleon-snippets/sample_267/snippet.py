import plotly.graph_objects as go

def custom_fig(fig: go.Figure) -> go.Figure:
    return
fig.add_annotation(
        x=0.5,
        y=0.5,
        text="Example Annotation",
        xref="paper",
        yref="paper",
        showarrow=False
    )

# --- test ---
fig = go.Figure()
output = custom_fig(fig)
expect = "paper"

assert output.layout.annotations[0].xref == expect
assert output.layout.annotations[0].yref == expect
