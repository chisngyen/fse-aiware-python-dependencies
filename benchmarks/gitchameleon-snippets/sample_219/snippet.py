import contextlib

class DummyServerConn:
    def __init__(self, sockname):
        self.sockname = sockname

class ConnectionLogger:
    pass
        

def solution() -> None:
    def
 server_connect(self, server_conn: DummyServerConn) -> None:
        print(server_conn.sockname)

    ConnectionLogger.server_connect = server_connect

# --- test ---

import unittest
import io
class TestConnectionLogger(unittest.TestCase):
    def test_server_connect(self):
        logger = ConnectionLogger()
        solution()
        dummy_conn = DummyServerConn(('127.0.0.1', 8080))
        
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            logger.server_connect(dummy_conn)
            
        expect = "('127.0.0.1', 8080)"
        
        self.assertIn(expect, output.getvalue())
        
unittest.main()
