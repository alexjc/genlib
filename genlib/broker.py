# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import asyncio
import collections


class CallbackSubscription:
    def __init__(self, channel, callback):
        self.channel = channel
        self._callback = callback

    async def process(self, message):
        await self._callback(self.channel.key, message)

    def cancel(self):
        pass


class QueueSubscription:
    def __init__(self, channel):
        self.channel = channel
        self._queue = asyncio.Queue()

    async def process(self, message):
        self._queue.put_nowait(message)

    async def get(self):
        if self._queue.qsize() == 0:
            await self.channel.provide()
        return await self._queue.get()

    def cancel(self):
        self._queue.put_nowait(None)


Provider = collections.namedtuple("Provider", ["function", "extra"])


class Channel:
    def __init__(self, key):
        self.key = key
        self.provider: Provider = None
        self.subscriptions = []

    async def provide(self):
        if self.provider is None:
            return

        await self.provider.function(self.key, **self.provider.extra)

    def close(self):
        for sub in self.subscriptions:
            sub.cancel()

        # Each of the listen() tasks unsubscribe themselves automatically.


class Broker:
    """Simple message broker that allows subscribing and publishing to channels.
    """

    def __init__(self):
        self._channels = {}

    def create_channel(self, key):
        assert key not in self._channels
        self._channels[key] = Channel(key)

    def destroy_channel(self, key):
        self._channels[key].close()
        del self._channels[key]

    def get_channel(self, key):
        assert key in self._channels
        return self._channels[key]

    def provide(self, channel_key, function, extra: dict = None):
        channel = self.get_channel(channel_key)
        channel.provider = Provider(function, extra or {})

    def register(self, channel_key, callback):
        channel = self.get_channel(channel_key)
        sub = CallbackSubscription(channel, callback)
        channel.subscriptions.append(sub)
        return sub

    def deregister(self, channel_key, callback):
        channel = self.get_channel(channel_key)
        for sub in channel.subscriptions:
            if getattr(sub, "_callback", None) == callback:
                channel.subscriptions.remove(sub)
                break

    async def publish(self, channel_key, message):
        channel = self.get_channel(channel_key)
        assert len(channel.subscriptions) > 0

        for sub in channel.subscriptions:
            await sub.process(message)

    async def receive(self, channel_key, subscription=None):
        try:
            sub = subscription or self.subscribe(channel_key)
            data = await sub.get()
        except asyncio.CancelledError:
            data = None
        finally:
            _ = subscription or self.unsubscribe(channel_key, sub)
        return data

    async def shutdown(self):
        for channel in self._channels.values():
            channel.close()
        self._channels = {}

    def get_subscription_count(self, channel_key):
        channel = self.get_channel(channel_key)
        return len(channel.subscriptions)

    def subscribe(self, channel_key):
        channel = self.get_channel(channel_key)
        sub = QueueSubscription(channel)
        channel.subscriptions.append(sub)
        return sub

    def unsubscribe(self, channel_key, sub):
        channel = self.get_channel(channel_key)
        channel.subscriptions.remove(sub)
