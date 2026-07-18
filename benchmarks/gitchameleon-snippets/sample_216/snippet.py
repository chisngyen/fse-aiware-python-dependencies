import time
import mitmproxy.connection as conn

def custom_client(ip_address: str, i_port: int, o_port: int) -> conn.Client:
    return
 conn.Client(
    peername=(ip_address, i_port),
    sockname=(ip_address, o_port),
    timestamp_start=time.time()
)

# --- test ---
ip_address = "127.0.0.1"
i_port = 111
o_port = 222
output_client = custom_client(ip_address, i_port, o_port)

expect_peername = ("127.0.0.1", 111)
expect_sockname = ("127.0.0.1", 222)

assert output_client.peername == expect_peername
assert output_client.sockname == expect_sockname
