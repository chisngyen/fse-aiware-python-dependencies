import falcon
from falcon import HTTPStatus


def custom_body(status: falcon.HTTPStatus, info:str) -> falcon.HTTPStatus:
    status.
text = info
    return status

# --- test ---
status = HTTPStatus(falcon.HTTP_200)
info = 'Falcon'

import warnings
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    resp = custom_body(status, info)
    if w:
        assert issubclass(w[-1].category, DeprecationWarning), "Expected a DeprecationWarning but got something else!"

expect = 'Falcon'
assert resp.text == expect
