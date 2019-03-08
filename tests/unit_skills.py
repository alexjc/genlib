# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import pytest

from genlib.skills import BaseSkill
from genlib.schema import Input, Output
from genlib.stream import Item


# All the tests in this file can be treated as asynchronous.
pytestmark = pytest.mark.asyncio


class TestBaseSkill:
    async def test_base_skill_raises_not_implemented_excetion(self):
        skill = BaseSkill()
        with pytest.raises(NotImplementedError):
            await skill.process()

    async def test_custom_skill_process_returns_one_output(self):
        class FakeSkill(BaseSkill):
            outputs = [Output("number", spec="int")]

            async def process(self):
                return {"number": Item(1234)}

        skill = FakeSkill()
        result = await skill.process()
        assert result["number"].data == 1234

    async def test_base_skill_clean_initialize_shutdown(self):
        skill = BaseSkill()
        await skill.on_initialize()
        await skill.on_shutdown()
