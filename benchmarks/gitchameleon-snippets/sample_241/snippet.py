from falcon import Response
import falcon

def custom_data(resp: falcon.Response, info: str) -> str:
    resp.data = info
    return
resp.render_body()

# --- test ---

class DummyResponse(Response):
    pass

info = "Falcon data"

resp = DummyResponse()
import warnings
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    rendered_body = custom_data(resp, info)
    if w:
        for warn in w:
            assert not issubclass(warn.category, DeprecationWarning), "Deprecated API used!"


expect = info
assert rendered_body == expect
