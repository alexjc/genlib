# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import pytest
import asyncio

from genlib.broker import Broker


# All the tests in this file can be treated as asynchronous.
pytestmark = pytest.mark.asyncio


@pytest.fixture
async def broker():
    b = Broker()
    b.create_channel("abcd")
    yield b
    await b.shutdown()

    for ch in b._channels.values():
        assert len(ch.subscriptions) == 0


class TestBrokerPassive:
    async def test_destroy_channel(self, broker):
        broker.destroy_channel("abcd")

    async def test_subscribe_unsubscribe(self, broker):
        sub = broker.subscribe("abcd")
        assert broker.get_subscription_count("abcd") == 1
        broker.unsubscribe("abcd", sub)
        assert broker.get_subscription_count("abcd") == 0

    async def test_publish_receive(self, broker):
        async def publish():
            await asyncio.sleep(0.01)
            await broker.publish("abcd", 1234)

        asyncio.create_task(publish())
        msg = await broker.receive("abcd")
        assert msg == 1234
        assert broker.get_subscription_count("abcd") == 0

    async def test_receive_cancel(self, broker):
        async def cancel():
            await asyncio.sleep(0.01)
            sub = broker._channels["abcd"].subscriptions[0]
            sub.cancel()
            await broker.publish("abcd", 1234)

        asyncio.create_task(cancel())
        msg = await broker.receive(channel_key="abcd")
        assert msg == None
        assert broker.get_subscription_count("abcd") == 0

    async def test_shutdown_unsubscribes(self, broker):
        async def listen():
            await broker.receive("abcd")

        task = asyncio.create_task(listen())
        await asyncio.sleep(0.01)
        await broker.shutdown()
        await asyncio.sleep(0.01)

        with pytest.raises(AssertionError):
            assert broker.get_subscription_count("abcd") == 0
        assert task.exception()


class TestBrokerActive:
    async def test_provides(self, broker):
        async def compute(value):
            await broker.publish("abcd", value)

        broker.register_provider("abcd", compute, value=1234)
        msg = await broker.receive(channel_key="abcd")
        assert msg == 1234

    async def test_callback_cancel(self, broker):
        async def callback(channel, message):
            pass

        sub = broker.add_callback("abcd", callback)
        sub.cancel()

        broker.remove_callback("abcd", callback)

    async def test_callback(self, broker):
        async def callback(channel, message):
            data.append((channel, message))

        data = []
        broker.add_callback("abcd", callback)
        await broker.publish("abcd", 5678)
        assert data == [("abcd", 5678)]

        broker.remove_callback("abcd", callback)
