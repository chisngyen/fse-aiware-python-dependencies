import pytest

def foo(a, b):
    return (10 * a - b + 7) // 3

@pytest.mark.parametrize(
    ["a", "b", "result"],
    [
        [1, 2, 5],
        [2, 3, 8],
        [5, 3, 18],
    ],
)
def test_foo(a: int, b: int, result: int) -> None:

    assert foo(a, b) == result

# --- test ---
import dis
import inspect
def test_assert_in_test_foo_bytecode():
    original_test_foo = inspect.unwrap(test_foo)
    instructions = list(dis.get_instructions(original_test_foo))
    has_raise = any(instr.opname == "RAISE_VARARGS" for instr in instructions)
    assert has_raise
    
test_assert_in_test_foo_bytecode()
