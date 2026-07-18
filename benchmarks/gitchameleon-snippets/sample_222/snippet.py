import contextlib

class DummyClientConn:
    def __init__(self, peername):
        self.peername = peername

class ConnectionLogger:
    pass

def solution() -> None:
    def
client_disconnected(self, client_conn) -> None:
        print(client_conn.peername)
        
    ConnectionLogger.client_disconnected = client_disconnected

# --- test ---
        
import unittest
import io
class TestConnectionLogger(unittest.TestCase):
    def test_client_disconnected(self):
        logger = ConnectionLogger()
        solution()
        dummy_conn = DummyClientConn(('127.0.0.1', 8080))
        
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            logger.client_disconnected(dummy_conn)
            
        expect = "('127.0.0.1', 8080)"
        
        self.assertIn(expect, output.getvalue())
        
unittest.main()
