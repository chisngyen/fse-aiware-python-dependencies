import json
from falcon import Request
from falcon.testing import create_environ

def custom_media(req: Request) -> dict[str, str]:
    return
req.get_media()

# --- test ---
import warnings

payload = {"key": "value"}
body_bytes = json.dumps(payload).encode("utf-8")

env = create_environ(
body=body_bytes,
headers={'Content-Type': 'application/json'}
)

req = Request(env)

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    media = custom_media(req)
    if w:
        for warn in w:
            assert not issubclass(warn.category, DeprecationWarning), "Deprecated API used!"
expect = payload
assert media == expect
