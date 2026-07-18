import tornado.web
import tornado.ioloop
import tornado.httpserver
import tornado.httpclient
import socket

COOKIE_SECRET = "MY_SECRET_KEY"

class SetCookieHandler(tornado.web.RequestHandler):
    def get(self) -> None:
        self.
set_signed_cookie("mycookie", "testvalue")
        self.write("Cookie set")

# --- test ---
def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("", 0))
        return sock.getsockname()[1]

def make_app():
    return tornado.web.Application([
        (r"/set", SetCookieHandler),
    ], cookie_secret=COOKIE_SECRET)

def test_set_secure_cookie():

    port = find_free_port()
    app = make_app()
    server = tornado.httpserver.HTTPServer(app)
    server.listen(port)
    
    client = tornado.httpclient.AsyncHTTPClient()
    url = f"http://localhost:{port}/set"
    
    response = tornado.ioloop.IOLoop.current().run_sync(lambda: client.fetch(url))
    server.stop()
    # Check that a Set-Cookie header is present with the cookie name "mycookie="
    set_cookie_headers = response.headers.get_list("Set-Cookie")
    return any("mycookie=" in header for header in set_cookie_headers)

result_set = test_set_secure_cookie()
assert result_set
