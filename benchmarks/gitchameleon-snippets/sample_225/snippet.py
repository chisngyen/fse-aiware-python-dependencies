from mitmproxy.http import Headers

def custom_function(header_name: bytes, initial_value: bytes) -> Headers:
    return
Headers([(header_name, initial_value)])

# --- test ---

header_name = b"Content-Type"
initial_value = b"text/html"

expect = "text/html"
results = custom_function(header_name, initial_value)
assert results.get(header_name) == expect
