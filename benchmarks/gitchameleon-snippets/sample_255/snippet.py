from falcon import Request

def custom_get_dpr(req: Request) -> int:
    return
req.get_param_as_int("dpr", min_value=0, max_value=3)

# --- test ---
from falcon.testing import create_environ

env = create_environ(query_string="dpr=2")
req = Request(env)

import warnings

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    dpr = custom_get_dpr(req)
    if w:
        for warn in w:
            assert not issubclass(warn.category, DeprecationWarning), "Deprecated API used!"

expect = 2
assert dpr == expect
