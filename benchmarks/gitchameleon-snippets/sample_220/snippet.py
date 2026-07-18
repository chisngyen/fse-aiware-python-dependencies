import contextlib

class DummyServerConn:
    def __init__(self, sockname):
        self.sockname = sockname

class ConnectionLogger:
    pass
        

def solution() -> None:
    def
server_disconnected(self, server_conn: DummyServerConn) -> None:
        print(server_conn.sockname)

    ConnectionLogger.server_disconnected = server_disconnected

# --- test ---

import unittest
import io
class TestConnectionLogger(unittest.TestCase):
    def test_server_disconnected(self):
        logger = ConnectionLogger()
        solution()
        dummy_conn = DummyServerConn(('127.0.0.1', 8080))
        
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            logger.server_disconnected(dummy_conn)
            
        expect = "('127.0.0.1', 8080)"
        
        self.assertIn(expect, output.getvalue())
        
unittest.main()
