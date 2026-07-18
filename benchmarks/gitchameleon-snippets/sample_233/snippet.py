import pytest

class CustomItem(pytest.Item):
    def __init__(
self, *, additional_arg, **kwargs):
        super().__init__(**kwargs)
        self.additional_arg = additional_arg

# --- test ---
import inspect
signature = inspect.signature(CustomItem.__init__)
assertion_value = any(param.kind == param.VAR_KEYWORD for param in signature.parameters.values())
assert assertion_value
