import asyncio
import os
import signal
from typing import Callable

def custom_add_callback_from_signal(callback: Callable[[], None], signum: int) -> None:
    loop =
asyncio.get_event_loop()
    loop.add_signal_handler(signum, callback)

# --- test ---

def test_custom_signal_handler():

    flag = {"executed": False}
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def callback():
        flag["executed"] = True
        loop.stop()

    custom_add_callback_from_signal(callback, signal.SIGUSR1)

    os.kill(os.getpid(), signal.SIGUSR1)

    loop.run_forever()

    return flag["executed"]

result = test_custom_signal_handler()
assert result
