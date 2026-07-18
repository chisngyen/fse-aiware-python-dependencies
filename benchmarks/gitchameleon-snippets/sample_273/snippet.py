import plotly
def custom_api_usage() -> str:
    import
chart_studio.api
    return chart_studio.api.__name__

# --- test ---
import warnings

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    module_name = custom_api_usage()
    for warn in w:
        assert not issubclass(warn.category, DeprecationWarning), "Deprecated API used!"

expect = "chart_studio.api"
assert module_name == expect
