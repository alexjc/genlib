# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import asyncio

from genlib.skills import BaseSkill


class Runner:
    """Manages the execution of a Skill until it has completed, calling initialize
    and shutdown appropriately.
    """

    def __init__(self, skill):
        self.skill = skill
        self._done = False

    async def run(self):
        yield (await self.skill.on_initialize())
        try:
            while not self._done:
                yield (await self.skill.process())
        finally:
            yield (await self.skill.on_shutdown())

    async def stop(self, task):
        self._done = True
        async for _ in task:
            break


class Scheduler:
    """Handles the execution of recipes, as a set of asynchronous coroutines.
    """

    def __init__(self):
        self._tasks = {}

    async def spawn(self, skill):
        runner = Runner(skill)
        task = runner.run()
        self._tasks[id(skill)] = (runner, task)

        async for _ in task:
            break

    async def tick(self, skill):
        _, task = self._tasks[id(skill)]
        async for result in task:
            return result

    async def halt(self, skill):
        runner, task = self._tasks.pop(id(skill))
        await runner.stop(task)

    async def shutdown(self):
        if len(self._tasks) > 0:
            await asyncio.wait([r.stop(t) for r, t in self._tasks.values()])
            self._tasks.clear()
