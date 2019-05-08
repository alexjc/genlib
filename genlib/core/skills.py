# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

from .meta import SkillConfigurator, provides, watching
from .schema import SkillInput, SkillOutput


__all__ = ["Skill", "Input", "Output", "provides", "watching"]


class BaseSkill(metaclass=SkillConfigurator):
    """Abstract base class for a generative skill.
    """

    inputs: "List[Input]" = []
    outputs: "List[Output]" = []

    def __init__(self):
        self.recipe = None  #: Parameters used to configure this skill instance.
        self.io = None  #: Interface for fetching inputs and providing outputs.

    async def on_initialize(self):
        pass

    async def on_shutdown(self):
        pass


Input = SkillInput
Output = SkillOutput
Skill = BaseSkill
