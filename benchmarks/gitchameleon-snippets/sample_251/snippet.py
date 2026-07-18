from typing import NoReturn
import falcon 


def raise_too_large_error(error_message: str) -> NoReturn:
    raise
falcon.HTTPPayloadTooLarge(error_message)

# --- test ---

error_message = "Request content is too large"

import warnings

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    try:
        raise_too_large_error(error_message)
    except falcon.HTTPPayloadTooLarge as e:
        exception_raised = e
    else:
        exception_raised = None

    if w:
        for warn in w:
            assert not issubclass(warn.category, DeprecationWarning), "Deprecated API used!"

expected_message = error_message
assert str(exception_raised) == expected_message
