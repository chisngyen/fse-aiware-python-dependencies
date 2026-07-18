class CustomRouter:
    def __init__(self):
        self.routes = {}

        
def solution() -> None:
    
    def add_route(
self, uri_template, resource, **kwargs):
        from falcon.routing import map_http_methods
        method_map = map_http_methods(resource, kwargs.get('fallback', None))
        self.routes[uri_template] = (resource, method_map)
        return method_map
    
    CustomRouter.add_route = add_route

# --- test ---
    
class DummyResource:
    def on_get(self, req, resp):
        resp.text = "hello"
import warnings
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    router = CustomRouter()
    solution()
    method_map = router.add_route("/test", DummyResource())
    if w:
        for warn in w:
            assert not issubclass(warn.category, DeprecationWarning), "Deprecated API used!"
            
expect = "/test"
assertion_value = expect in router.routes
assert assertion_value
resource, mapping = router.routes["/test"]
assertion_value = callable(mapping.get("GET", None)) 
assert assertion_value
