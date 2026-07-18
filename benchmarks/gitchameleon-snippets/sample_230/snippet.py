import pytest
import pathlib

@pytest.hookimpl()
def pytest_pycollect_makemodule(
module_path:pathlib.Path):
    pass

# --- test ---
import inspect
def test_pytest_pycollect_makemodule_signature():
    sig = inspect.signature(pytest_pycollect_makemodule)
    params = list(sig.parameters.items())
    name, param = params[0]
    expect = pathlib.Path
    assert param.annotation == expect

test_pytest_pycollect_makemodule_signature()
