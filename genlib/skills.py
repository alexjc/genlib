# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.


class BaseSkill:
    """Abstract base class for a generative skill.
    """

    inputs = []
    outputs = []

    async def process(self):
        pass
