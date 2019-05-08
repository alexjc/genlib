# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import pytest

from genlib.core.skills import Skill, Output
from genlib.runtime.scheduler import Scheduler


class FakeSkill(Skill):
    outputs = [Output("test", spec="int")]

    async def on_initialize(self):
        self.counter = 0

    async def process(self):
        self.counter += 1
        return {"test": self.counter * 123}

    async def on_shutdown(self):
        self.counter = -1


class ProblemSkill(Skill):
    outputs = [Output("wrong", spec="float")]

    async def process(self):
        raise NotImplementedError


@pytest.fixture
def fake_skill():
    yield FakeSkill()


@pytest.fixture
async def scheduler():
    s = Scheduler()
    yield s
    await s.shutdown()


# All the tests in this file can be treated as asynchronous.
pytestmark = pytest.mark.asyncio


class TestScheduleSingleTask:
    async def test_correctly_spawns_halts(self, scheduler, fake_skill):
        await scheduler.spawn(fake_skill)
        assert scheduler.get_active_skill_count() == 1
        assert fake_skill in scheduler.list_active_skills()

        await scheduler.halt(fake_skill)
        assert scheduler.get_active_skill_count() == 0
        assert fake_skill not in scheduler.list_active_skills()

    async def test_premature_halt_throws_exception(self, scheduler, fake_skill):
        with pytest.raises(KeyError):
            await scheduler.halt(fake_skill)
        assert fake_skill not in scheduler.list_active_skills()

    async def test_unknown_tick_throws_exception(self, scheduler, fake_skill):
        with pytest.raises(KeyError):
            await scheduler.step(fake_skill, FakeSkill.process)
        assert fake_skill not in scheduler.list_active_skills()

    async def test_correctly_ticks_multiple_times(self, scheduler, fake_skill):
        await scheduler.spawn(fake_skill)
        for i in range(1, 10):
            result = await scheduler.step(fake_skill, FakeSkill.process)
            assert result == {"test": i * 123}
        await scheduler.halt(fake_skill)

    async def test_correctly_ticks_calls_observer(self, scheduler, fake_skill):
        async def observe(skill, result):
            outputs.append((skill, result))

        outputs = []
        scheduler.on_compute = observe
        await scheduler.spawn(fake_skill)
        for i in range(1, 5):
            await scheduler.step(fake_skill, FakeSkill.process)
            assert outputs[-1] == (fake_skill, {"test": i * 123})

        assert len(outputs) == 4

    async def test_spawn_correctly_calls_on_initialize(self, scheduler, fake_skill):
        assert not hasattr(fake_skill, "counter")
        await scheduler.spawn(fake_skill)
        assert fake_skill.counter == 0

    async def test_halt_correctly_calls_on_shutdown(self, scheduler, fake_skill):
        await scheduler.spawn(fake_skill)
        await scheduler.halt(fake_skill)
        assert fake_skill.counter == -1


@pytest.fixture
def problem_skill():
    yield ProblemSkill()


class TestSchedulerErrorHandling:
    async def test_exception_is_caught(self, scheduler, problem_skill):
        await scheduler.spawn(problem_skill)
        with pytest.raises(NotImplementedError):
            await scheduler.step(problem_skill, ProblemSkill.process)
