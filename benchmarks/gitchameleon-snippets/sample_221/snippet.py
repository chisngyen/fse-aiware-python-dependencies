import contextlib

class DummyClientConn:
    def __init__(self, peername):
        self.peername = peername

class ConnectionLogger:
    pass

def solution() -> None:
    def
client_connected(self, client_conn: DummyClientConn) -> None:
        print(client_conn.peername)

    ConnectionLogger.client_connected = client_connected

# --- test ---
    
import unittest
import io
class TestConnectionLogger(unittest.TestCase):
    def test_client_connected(self):
        logger = ConnectionLogger()
        solution()
        dummy_conn = DummyClientConn(('127.0.0.1', 8080))
        
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            logger.client_connected(dummy_conn)
            
        expect = "('127.0.0.1', 8080)"
        
        self.assertIn(expect, output.getvalue())
        
unittest.main()
