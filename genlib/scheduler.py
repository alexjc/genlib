# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import asyncio

from genlib.skills import BaseSkill


class Runner:
    """Manages the execution of a Skill until it has completed, calling initialize
    and shutdown appropriately.
    """

    def __init__(self, skill):
        self.skill = skill
        self.done = False
        self.generator = self.run()

    async def run(self):
        yield (await self.skill.on_initialize())
        try:
            while not self.done:
                yield (await self.skill.process())
        except Exception as exc:
            yield exc
        finally:
            yield (await self.skill.on_shutdown())

    async def start(self):
        # Wait for `on_initialize` message from run().
        async for _ in self.generator:
            break

    async def stop(self):
        self.done = True
        # Pause until `on_shutdown` is done from run().
        async for _ in self.generator:
            break


class Scheduler:
    """Handles the execution of recipes, as a set of asynchronous coroutines.
    """

    def __init__(self, on_compute=None):
        self._runners = {}
        self.on_compute = on_compute

    async def spawn(self, skill):
        runner = Runner(skill)
        await runner.start()
        self._runners[id(skill)] = runner

    async def tick(self, skill, output=None):
        runner = self._runners[id(skill)]
        async for result in runner.generator:
            if isinstance(result, Exception):
                raise result

            if self.on_compute is not None:
                await self.on_compute(skill, result)
            return result

    def list_active_skills(self):
        """Reverse iterator over the skills that are currently active.
        """
        for runner in reversed(list(self._runners.values())):
            yield runner.skill

    def get_active_skill_count(self):
        return len(self._runners)

    async def halt(self, skill):
        runner = self._runners.pop(id(skill))
        await runner.stop()

    async def shutdown(self):
        if len(self._runners) > 0:
            await asyncio.wait([r.stop() for r in self._runners.values()])
            self._runners.clear()
