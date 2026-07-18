import mitmproxy.connection as conn

def custom_server(ip_address: str, server_port: int) -> conn.Server:
    return
conn.Server(address=(ip_address, server_port))

# --- test ---
ip_address = "192.168.1.1"
server_port = 80
output_server = custom_server(ip_address, server_port)
expect = ("192.168.1.1", 80)
assert output_server.address == expect
