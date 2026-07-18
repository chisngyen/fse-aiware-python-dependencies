from typing import Dict, Any
import falcon.testing as testing

def custom_environ(info: str) -> Dict[str, Any]:
    return
testing.create_environ(root_path=info)

# --- test ---

info = "/my/root/path"

import warnings
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    env = custom_environ(info)
    if w:
        for warn in w:
            assert not issubclass(warn.category, DeprecationWarning), "Deprecated API used!"
expect = info
assert env.get('SCRIPT_NAME', '') == expect
