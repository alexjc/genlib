# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import asyncio
import itertools
import collections


class Subscription:
    def __init__(self):
        self._queue = asyncio.Queue()
        self._task = asyncio.current_task()


class Broker:
    """Simple message broker that allows subscribing and publishing to channels.
    """

    def __init__(self):
        self._subscriptions = collections.defaultdict(list)

    async def publish(self, channel, message):
        for sub in self._subscriptions[channel]:
            sub._queue.put_nowait(message)

    async def listen(self, channel=None, subscription=None):
        try:
            sub = subscription or self.subscribe(channel)
            while True:
                data = await sub._queue.get()
                yield data
        except asyncio.CancelledError:
            pass
        finally:
            subscription or self.unsubscribe(channel, sub)

    async def receive(self, channel=None, subscription=None):
        sub = subscription or self.subscribe(channel)
        try:
            data = await sub._queue.get()
        except asyncio.CancelledError:
            data = None
        finally:
            subscription or self.unsubscribe(channel, sub)
        return data

    def cancel(self, sub):
        sub._task.cancel()

    async def shutdown(self):
        for sub in itertools.chain(*self._subscriptions.values()):
            self.cancel(sub)
        # Each of the listen() tasks should unsubscribe itself automatically.

    def get_subscription_count(self, channel):
        return len(self._subscriptions[channel])

    def subscribe(self, channel):
        sub = Subscription()
        self._subscriptions[channel].append(sub)
        return sub

    def unsubscribe(self, channel, sub):
        self._subscriptions[channel].remove(sub)
