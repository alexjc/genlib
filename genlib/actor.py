# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

from .interpreter import Interpreter
from .stream import Item


class Actor:
    def __init__(self, registry, listing):
        self.registry = registry
        self.listing = listing

        self.interpreter = Interpreter()
        self.skills = []

    async def shutdown(self):
        await self.interpreter.shutdown()

    def get_listing(self):
        return self.listing

    async def push_skill_input(self, skill, key, value):
        await self.interpreter.push_skill_input(skill, key, Item(value))

    async def pull_skill_output(self, skill, key):
        return await self.interpreter.pull_skill_output(skill, key)

    async def invoke(self, command, parameters):
        uri = self.listing[command]
        schema = self.registry.find_skill_schema(uri)
        skill = self.registry.construct(schema)

        await self.interpreter.launch(skill)
        self.skills.append(skill)
        return skill

    async def revoke(self, skill):
        self.skills.remove(skill)
        await self.interpreter.abort(skill)
