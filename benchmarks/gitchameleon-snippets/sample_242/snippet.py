import falcon
from falcon import HTTPError


def custom_http_error(title: str, description: str) -> bytes:
    return
HTTPError(falcon.HTTP_400, title, description).to_json()

# --- test ---
title = "Bad Request"
description = "An error occurred"
import warnings
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    result = custom_http_error(title, description)
    if w:
        for warn in w:
            assert not issubclass(warn.category, DeprecationWarning), "Deprecated API used!"


expect = b'{"title": "Bad Request", "description": "An error occurred"}'
assert result == expect
