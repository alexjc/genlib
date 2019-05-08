# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import pytest

from genlib.core.skills import Skill, Input, Output, watching, provides
from genlib.core.stream import Item


class TestConfiguration:
    def test_base_skill_raises_not_implemented_excetion(self):
        with pytest.raises(AssertionError):

            class EmptySkill(Skill):
                pass

            _ = EmptySkill()

    @pytest.mark.asyncio
    async def test_custom_skill_process_returns_one_output(self):
        class FakeSkill(Skill):
            outputs = [Output("number", spec="int")]

            async def my_process(self):
                return {"number": Item(1234)}

        skill = FakeSkill()
        result = await skill.my_process()
        assert result["number"].data == 1234

    def test_skill_watching_decorator(self):
        class ReactiveSkill(Skill):
            inputs = [Output("value", spec="int")]
            outputs = [Output("number", spec="int")]

            @watching("value")
            def compute(self):
                pass

        skill = ReactiveSkill()
        assert len(skill.methods_watching["value"]) == 1
        assert skill.methods_watching["value"] == [ReactiveSkill.compute]

    def test_skill_provides_decorator(self):
        class AnnotatedSkill(Skill):
            outputs = [Output("number", spec="int")]

            @provides("number")
            def do(self):
                pass

        skill = AnnotatedSkill()
        assert "number" in skill.method_providing
        assert skill.method_providing["number"] == AnnotatedSkill.do

    @pytest.mark.asyncio
    async def test_base_skill_clean_initialize_shutdown(self):
        skill = Skill()
        await skill.on_initialize()
        await skill.on_shutdown()
