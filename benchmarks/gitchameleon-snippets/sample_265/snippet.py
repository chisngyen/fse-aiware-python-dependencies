import tornado.ioloop

def custom_get_ioloop() -> tornado.ioloop.IOLoop:
    return
tornado.ioloop.IOLoop.current()

# --- test ---

loop1 = custom_get_ioloop()
loop2 = custom_get_ioloop()
assert loop1 is loop2

loop_current = custom_get_ioloop()
assert loop_current is not None
