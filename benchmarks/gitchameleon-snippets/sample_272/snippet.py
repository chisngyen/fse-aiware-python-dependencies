import plotly
def custom_chart_studio_usage() -> bool:
    import
chart_studio.plotly
    return hasattr(chart_studio.plotly, "plot")

# --- test ---
import warnings
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    has_plot = custom_chart_studio_usage()
    for warn in w:
        assert not issubclass(warn.category, DeprecationWarning), "Deprecated API used!"

assert has_plot
