# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import pytest
import asyncio

from genlib.stream import Item
from genlib.interpreter import Interpreter
from genlib.skills import Skill, Input, Output, watching


# All the tests in this file can be treated as asynchronous.
pytestmark = pytest.mark.asyncio


class PassiveSkill(Skill):

    inputs = [Input("A", spec="int")]
    outputs = [Output("B", spec="int")]

    async def process(self):
        a, = await self.io.pull_inputs("A")
        return {"B": Item(data=a.data + 1)}


class ReactiveSkill(Skill):

    inputs = [Input("C", spec="int")]
    outputs = [Output("D", spec="int")]

    @watching("C")
    async def process(self):
        c, = await self.io.pull_inputs("C")
        return {"D": Item(data=c.data - 1)}


@pytest.fixture
def passive_skill():
    yield PassiveSkill()


@pytest.fixture
def reactive_skill():
    yield ReactiveSkill()


@pytest.fixture
async def interpreter():
    interpreter = Interpreter()
    yield interpreter
    await interpreter.shutdown()


class TestInterpreterOneSkill:
    async def test_launch_abort(self, interpreter, passive_skill):
        await interpreter.launch(passive_skill)
        assert (passive_skill, "A") in interpreter.subscriptions
        await interpreter.abort(passive_skill)

    async def test_wait_for_pull(self, interpreter, passive_skill):
        await interpreter.launch(passive_skill)
        await interpreter.push_skill_input(passive_skill, "A", Item(1000))
        assert interpreter.subscriptions[(passive_skill, "A")]._queue.qsize() == 1

        result = await interpreter.pull_skill_output(passive_skill, "B")
        assert result.data == 1001
        assert interpreter.subscriptions[(passive_skill, "A")]._queue.qsize() == 0

    async def test_triggered_on_push(self, interpreter, reactive_skill):
        await interpreter.launch(reactive_skill)
        sub = interpreter.broker.subscribe((reactive_skill, "D"))

        await interpreter.push_skill_input(reactive_skill, "C", Item(1000))
        assert interpreter.subscriptions[(reactive_skill, "C")]._queue.qsize() == 0

        result = await sub.get()
        assert result.data == 999

    # 1-in-1-out
    #   skill that actively pulls value

    # 1-in-2-out
    #   multiple different functions to compute both output


class TestInterpreterTwoSkills:
    async def __test_launch_abort(self, interpreter):
        skills = [PassiveSkill() for _ in range(2)]
        [await interpreter.launch(s) for s in skills]
        assert (skills[0], "A") in interpreter.subscriptions
        assert (skills[1], "A") in interpreter.subscriptions
        [await interpreter.abort(s) for s in skills]

    async def test_wait_for_pull(self, interpreter):
        skills = [PassiveSkill() for _ in range(2)]
        [await interpreter.launch(s) for s in skills]

        interpreter.connect(skills[0], "B", skills[1], "A")

        assert len(interpreter.broker._channels[(skills[0], "B")].subscriptions) == 1

        await interpreter.push_skill_input(skills[0], "A", Item(1000))
        assert interpreter.subscriptions[(skills[0], "A")]._queue.qsize() == 1
        assert interpreter.subscriptions[(skills[1], "A")]._queue.qsize() == 0

        result = await interpreter.pull_skill_output(skills[1], "B")
        assert len(interpreter.broker._channels[(skills[0], "B")].subscriptions) == 1

        assert result.data == 1002
        assert interpreter.subscriptions[(skills[0], "A")]._queue.qsize() == 0
        assert interpreter.subscriptions[(skills[1], "A")]._queue.qsize() == 0

        [await interpreter.abort(s) for s in skills]

