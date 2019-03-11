# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

from .schema import SkillInput, SkillOutput


Input = SkillInput
Output = SkillOutput


class BaseSkill:
    """Abstract base class for a generative skill.
    """

    inputs = []
    outputs = []

    async def on_initialize(self):
        pass

    async def on_shutdown(self):
        pass

    async def process(self):
        raise NotImplementedError
