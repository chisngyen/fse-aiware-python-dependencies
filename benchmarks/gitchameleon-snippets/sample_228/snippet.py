import pytest
import pathlib

@pytest.hookimpl()
def pytest_ignore_collect(
collection_path:pathlib.Path):
    pass

# --- test ---
import inspect
def test_pytest_ignore_collect_signature():
    sig = inspect.signature(pytest_ignore_collect)
    params = list(sig.parameters.items())
    name, param = params[0]
    expect = pathlib.Path
    assert param.annotation == expect

test_pytest_ignore_collect_signature()
