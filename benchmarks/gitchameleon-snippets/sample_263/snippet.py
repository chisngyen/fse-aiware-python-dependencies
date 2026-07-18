import asyncio
import tornado.auth
import asyncio

class DummyAuth(tornado.auth.OAuth2Mixin):
    async def async_get_user_info(self, access_token: str) -> dict[str, str]:
        return
{"user": "test", "token": access_token}

# --- test ---
async def custom_auth_test():
    auth = DummyAuth()
    result = await auth.async_get_user_info("dummy_token")
    expect = "dummy_token"
    assert result['token'] == expect

async def main():
    result = await custom_auth_test()

if __name__ == "__main__":
    asyncio.run(main())
