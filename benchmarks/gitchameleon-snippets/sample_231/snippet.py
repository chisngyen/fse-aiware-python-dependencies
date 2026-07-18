import pytest
import pathlib

@pytest.hookimpl()
def pytest_report_header(
start_path:pathlib.Path):
    pass

# --- test ---

import inspect
def test_pytest_report_header_signature():
    sig = inspect.signature(pytest_report_header)
    params = list(sig.parameters.items())
    name, param = params[0]
    expect = pathlib.Path
    assert param.annotation == expect

test_pytest_report_header_signature()
