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

    async def publish(self, channel, data):
        for sub in self._subscriptions[channel]:
            sub._queue.put_nowait(data)

    async def listen(self, channel):
        try:
            sub = self._subscribe(channel)
            while True:
                try:
                    data = await sub._queue.get()
                    yield data
                except asyncio.CancelledError:
                    break
        finally:
            self._unsubscribe(channel, sub)

    def cancel(self, sub):
        sub._task.cancel()

    async def shutdown(self):
        for sub in itertools.chain(*self._subscriptions.values()):
            self.cancel(sub)
        # Each of the listen() tasks should unsubscribe itself automatically.

    def get_subscription_count(self, channel):
        return len(self._subscriptions[channel])

    def _subscribe(self, channel):
        sub = Subscription()
        self._subscriptions[channel].append(sub)
        return sub

    def _unsubscribe(self, channel, sub):
        self._subscriptions[channel].remove(sub)
