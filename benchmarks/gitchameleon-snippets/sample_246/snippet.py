from typing import Dict, Any
import falcon.testing as testing

def custom_environ(v: str) -> Dict[str, Any]:
    return
testing.create_environ(http_version=v)

# --- test ---
import warnings

version = "1.1"
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    env = custom_environ(version)
    if w:
        for warn in w:
            assert not issubclass(warn.category, DeprecationWarning), "Deprecated API used!"

expect = "HTTP/1.1"
assert env.get('SERVER_PROTOCOL', '') == expect
