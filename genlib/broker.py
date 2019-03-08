# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import asyncio
import collections


class Subscription:
    def __init__(self):
        self._queue = asyncio.Queue()


class Broker:
    """Simple message broker that allows subscribing and publishing to channels.
    """

    def __init__(self):
        self._subscriptions = collections.defaultdict(list)

    async def publish(self, channel, data):
        for sub in self._subscriptions[channel]:
            sub._queue.put_nowait(data)

    async def listen(self, channel):
        try:
            sub = self._subscribe(channel)
            while True:
                data = await sub._queue.get()
                yield data
        finally:
            self._unsubscribe(channel, sub)

    async def shutdown(self):
        pass

    def get_subscription_count(self, channel):
        return len(self._subscriptions[channel])

    def _subscribe(self, channel):
        sub = Subscription()
        self._subscriptions[channel].append(sub)
        return sub

    def _unsubscribe(self, channel, sub):
        self._subscriptions[channel].remove(sub)
