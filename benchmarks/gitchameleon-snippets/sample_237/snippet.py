from falcon import stream

import io
class DummyRequest:
    def __init__(self, data: bytes):
        self.stream = io.BytesIO(data)
        self.content_length = len(data)


def get_bounded_stream(req: DummyRequest) -> stream.BoundedStream:
    return
stream.BoundedStream(req.stream, req.content_length)

# --- test ---
test_data = b"Hello, Falcon!"
req = DummyRequest(test_data)

bounded_stream = get_bounded_stream(req)
read_data = bounded_stream.read()
expect = b"Hello, Falcon!"
assert read_data == expect
