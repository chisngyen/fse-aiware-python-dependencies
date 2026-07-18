import contextlib

class DummyServerConn:
    def __init__(self, sockname):
        self.sockname = sockname

class ConnectionLogger:
    pass
        

def solution() -> None:
    def
 server_connected(self, server_conn: DummyServerConn) -> None:
        print(server_conn.sockname)

    ConnectionLogger.server_connected = server_connected

# --- test ---
    
import unittest
import io

class TestConnectionLogger(unittest.TestCase):
    def test_server_connected(self):
        # Update the ConnectionLogger class with the new method.
        solution()
        logger = ConnectionLogger()
        dummy_conn = DummyServerConn(('127.0.0.1', 8080))
        
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            logger.server_connected(dummy_conn)
        print(output.getvalue())
        expect = "('127.0.0.1', 8080)"
        
        self.assertIn(expect, output.getvalue())
        
unittest.main()
