import falcon

def custom_falcons() -> falcon.App:
    return
falcon.App()

# --- test ---
import warnings
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    app_instance = custom_falcons()
    if w:
        for warn in w:
            assert not issubclass(warn.category, DeprecationWarning), "Deprecated API used!"

expect = falcon.App
assert isinstance(app_instance, expect)
