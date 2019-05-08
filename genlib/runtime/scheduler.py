# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import asyncio


class Runner:
    """Manages the execution of a Skill until it has completed, calling initialize
    and shutdown appropriately.
    """

    def __init__(self, skill):
        self.skill = skill
        self.request_queue = asyncio.Queue()
        self.result_queue = asyncio.Queue()
        self._task = None

    async def step(self, function):
        self.request_queue.put_nowait(function)
        return await self.result_queue.get()

    async def run(self):
        await self.skill.on_initialize()
        self.result_queue.put_nowait("initialize")
        try:
            while True:
                function = await self.request_queue.get()
                result = await function(self.skill)
                await self.result_queue.put(result)
        except asyncio.CancelledError:
            pass
        except Exception as exc:  # pylint: disable=broad-except
            self.result_queue.put_nowait(exc)
        finally:
            await self.skill.on_shutdown()
            self.result_queue.put_nowait("shutdown")

    async def start(self):
        self._task = asyncio.create_task(self.run())
        await self.result_queue.get()

    async def stop(self):
        self._task.cancel()
        await self.result_queue.get()


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

    async def step(self, skill, function):
        runner = self._runners[id(skill)]
        result = await runner.step(function)
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
