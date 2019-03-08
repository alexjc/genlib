# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import pytest
import asyncio

from genlib.broker import Broker


# All the tests in this file can be treated as asynchronous.
pytestmark = pytest.mark.asyncio


@pytest.fixture
async def broker():
    b = Broker()
    yield b
    await b.shutdown()


class TestBroker:
    async def test_subscribe_unsubscribe(self, broker):
        sub = broker._subscribe("abcd")
        assert broker.get_subscription_count("abcd") == 1
        broker._unsubscribe("abcd", sub)
        assert broker.get_subscription_count("abcd") == 0

    async def test_listen_publish(self, broker):
        async def publish():
            await asyncio.sleep(0.01)
            await broker.publish("abcd", 1234)

        asyncio.create_task(publish())

        async for msg in broker.listen("abcd"):
            assert msg == 1234
            assert broker.get_subscription_count("abcd") == 1
            break

        await asyncio.sleep(0.01)
        assert broker.get_subscription_count("abcd") == 0

    async def test_listen_cancel(self, broker):
        async def cancel():
            await asyncio.sleep(0.01)
            sub = broker._subscriptions["abcd"][0]
            broker.cancel(sub)
            await broker.publish("abcd", 1234)

        asyncio.create_task(cancel())

        cancelled = None
        async for _ in broker.listen("abcd"):
            assert False, "The subscription was not cancelled."
        else:
            cancelled = True
        assert cancelled is True

    async def test_shutdown_unsubscribes(self, broker):
        async def listen():
            async for _ in broker.listen("abcd"):
                pass

        asyncio.create_task(listen())
        await broker.shutdown()

        assert broker.get_subscription_count("abcd") == 0
