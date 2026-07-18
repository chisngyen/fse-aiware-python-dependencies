from falcon import Request
from falcon.util.structures import Context


def custom_set_context(req: Request, role: str, user: str) -> Context:
    req.
context.role = role
    req.context.user = user
    return req.context

# --- test ---
from falcon.testing import create_environ

env = create_environ()
req = Request(env)
role = 'trial'
user = 'guest'
import warnings

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    context = custom_set_context(req, role, user)
    if w:
        for warn in w:
            assert not issubclass(warn.category, DeprecationWarning), "Deprecated API used!"

expect1 = 'trial'
expect2 = 'guest'

assert context.role == expect1
assert context.user == expect2
