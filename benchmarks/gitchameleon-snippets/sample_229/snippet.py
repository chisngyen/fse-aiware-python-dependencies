import pytest
import pathlib

@pytest.hookimpl()
def pytest_collect_file(
file_path:pathlib.Path):
    pass

# --- test ---

import inspect
def test_pytest_collect_file_signature():
    sig = inspect.signature(pytest_collect_file)
    params = list(sig.parameters.items())
    name, param = params[0]
    expect = pathlib.Path
    assert param.annotation == expect

test_pytest_collect_file_signature()
