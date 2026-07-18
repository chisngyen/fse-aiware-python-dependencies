import contextlib

class DummyLogEntry:
    def __init__(self, msg):
        self.msg = msg

class MyAddon:
    pass

def solution() -> None:
    def
add_log(self, entry):
        print(f"{entry.msg}")
    
    MyAddon.add_log = add_log

# --- test ---
    
import unittest
import io
class TestMyAddonLogging(unittest.TestCase):
    def test_logging_event(self):
        addon = MyAddon()
        solution()
        dummy_entry = DummyLogEntry("Test log message")
        
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            addon.add_log(dummy_entry)
        print(output.getvalue())
        expect = "Test log message"
        self.assertIn(expect, output.getvalue())

unittest.main()
