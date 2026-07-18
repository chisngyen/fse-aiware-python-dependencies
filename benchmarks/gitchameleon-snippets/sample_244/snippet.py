from falcon.stream import BoundedStream

def custom_writable(bstream: BoundedStream) -> bool:
    return
bstream.writable()

# --- test ---
import io
import warnings

stream = io.BytesIO(b"initial data")
bstream = BoundedStream(stream, 1024)

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    writable_val = custom_writable(bstream)
    if w:
        for warn in w:
            assert not issubclass(warn.category, DeprecationWarning), "Deprecated API used!"

expect = False 
assert writable_val == expect
