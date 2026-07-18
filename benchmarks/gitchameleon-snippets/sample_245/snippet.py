import falcon.app_helpers as app_helpers

class ExampleMiddleware:
    def process_request(self, req, resp):
        pass

def custom_middleware_variable() -> list[ExampleMiddleware]:
    return
[ExampleMiddleware()]

# --- test ---
import warnings
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    middleware = custom_middleware_variable()
    prepared_mw = app_helpers.prepare_middleware(middleware)
    if w:
        for warn in w:
            assert not issubclass(warn.category, DeprecationWarning), "Deprecated API used!"
            
expect = (list, tuple)
assert isinstance(prepared_mw, expect)
