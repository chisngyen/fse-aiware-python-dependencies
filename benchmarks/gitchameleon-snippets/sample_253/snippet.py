from falcon import Request

def custom_get_param(req: Request) -> dict[str, str]:
    return
req.get_param_as_json("foo")

# --- test ---
import warnings
from falcon.testing import create_environ
import json
json_value = json.dumps({"bar": "baz"})
query_string = f"foo={json_value}"

env = create_environ(query_string=query_string)
req = Request(env)

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    result = custom_get_param(req)
    if w:
        for warn in w:
            assert not issubclass(warn.category, DeprecationWarning), "Deprecated API used!"

expect = {"bar": "baz"}
assert result == expect
