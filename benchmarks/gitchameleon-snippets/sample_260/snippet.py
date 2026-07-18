import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.websocket
import tornado.httpclient
import socket

async def custom_websocket_connect(url: str, resolver: tornado.netutil.Resolver ) -> tornado.websocket.WebSocketClientConnection:

    return await
tornado.websocket.websocket_connect(url, resolver=resolver)

# --- test ---
class EchoWebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print("WebSocket opened")

    def on_message(self, message):
        self.write_message(message)

    def on_close(self):
        print("WebSocket closed")

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("", 0))
        return sock.getsockname()[1]

def test_websocket_large_message():

    resolver = None

    app = tornado.web.Application([
        (r"/ws", EchoWebSocketHandler),
    ])
    port = find_free_port()
    server = tornado.httpserver.HTTPServer(app)
    server.listen(port)

    ws_url = f"ws://localhost:{port}/ws"

    large_message = "A" * 100000  # 100k characters

    async def run_test():
        conn = await custom_websocket_connect(ws_url, resolver)
        conn.write_message(large_message)
        echoed = await conn.read_message()
        conn.close()
        return echoed == large_message

    result = tornado.ioloop.IOLoop.current().run_sync(run_test)

    server.stop()
    return result

result = test_websocket_large_message()
assert result
