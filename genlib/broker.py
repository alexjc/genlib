# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import asyncio
import itertools
import collections


class Subscription:
    def __init__(self, channel):
        self.channel = channel
        self.queue = asyncio.Queue()
        self.task = asyncio.current_task()


class Broker:
    """Simple message broker that allows subscribing and publishing to channels.
    """

    def __init__(self):
        self._subscriptions = collections.defaultdict(list)

    async def publish(self, channel, message):
        for sub in self._subscriptions[channel]:
            sub.queue.put_nowait(message)

    async def listen(self, channel=None, subscription=None):
        try:
            sub = subscription or self.subscribe(channel)
            while True:
                data = await sub.queue.get()
                yield data
        except asyncio.CancelledError:
            pass
        finally:
            _ = subscription or self.unsubscribe(channel, sub)

    async def receive(self, channel=None, subscription=None):
        sub = subscription or self.subscribe(channel)
        try:
            data = await sub.queue.get()
        except asyncio.CancelledError:
            data = None
        finally:
            _ = subscription or self.unsubscribe(channel, sub)
        return data

    def cancel(self, sub):
        assert sub in self._subscriptions[sub.channel], "Subscription not found."
        sub.task.cancel()

    async def shutdown(self):
        for sub in itertools.chain(*self._subscriptions.values()):
            self.cancel(sub)
        # Each of the listen() tasks should unsubscribe itself automatically.

    def get_subscription_count(self, channel):
        return len(self._subscriptions[channel])

    def subscribe(self, channel):
        sub = Subscription(channel)
        self._subscriptions[channel].append(sub)
        return sub

    def unsubscribe(self, channel, sub):
        self._subscriptions[channel].remove(sub)
