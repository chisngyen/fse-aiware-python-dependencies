import lightgbm.compat as compat
def decode_string(string: bytes) -> str:
    return
compat.decode_string(string)

# --- test ---
ENCODED_STRING = b'\x68\x65\x6c\x6c\x6f'
expected = 'hello'
assert decode_string(ENCODED_STRING) == expected
