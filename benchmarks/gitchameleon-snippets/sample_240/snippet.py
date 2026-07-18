from falcon import Response

def custom_body_length(resp: Response, info):
    resp.
content_length = len(info)
    return resp

# --- test ---

info = "Falcon"

class DummyResponse(Response):
    pass

resp = DummyResponse()

import warnings
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    custom_resp = custom_body_length(resp, info)
    if w:
        for warn in w:
            assert not issubclass(warn.category, DeprecationWarning), "Deprecated API used!"
expect = str(6)
assert custom_resp.content_length == expect
