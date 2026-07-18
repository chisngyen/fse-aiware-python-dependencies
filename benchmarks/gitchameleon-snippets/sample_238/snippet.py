import falcon


def custom_body(resp: falcon.Response, info: str) -> falcon.Response:
    resp.
text = info
    return resp

# --- test ---
resp = falcon.Response()
info = 'Falcon'

import warnings
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    resp = custom_body(resp, info)
    if w:
        assert issubclass(w[-1].category, DeprecationWarning), "Expected a DeprecationWarning but got something else!"

expect = 'Falcon'
assert resp.text == expect
