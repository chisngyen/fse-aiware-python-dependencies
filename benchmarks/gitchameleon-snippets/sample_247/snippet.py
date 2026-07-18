from falcon import Response
import falcon

def custom_append_link(resp: falcon.Response, link: str, rel: str) -> falcon.Response:
    resp.
append_link(link, rel, crossorigin='anonymous')
    return resp

# --- test ---
resp = Response()
link = 'http://example.com'
rel = 'preconnect'

response = custom_append_link(resp, link, rel)
expected = "crossorigin"
assert expected in response.get_header('Link')
