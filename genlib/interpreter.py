# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

from .broker import Broker
from .scheduler import Scheduler


class Facade:
    """Simplified interface to the Interpreter that's bound to a specific Skill,
    allowing it to easily pull inputs and push outputs.
    """

    def __init__(self, interpreter, skill):
        self._interpreter = interpreter
        self._skill = skill

    async def pull_inputs(self, *keys):
        return [await self._interpreter.pull_skill_input(self._skill, k) for k in keys]


class Interpreter:
    """Manages the execution and communication of multiple skills.
    """

    def __init__(self, broker=None, scheduler=None):
        self.broker = broker or Broker()
        self.scheduler = scheduler or Scheduler()

        self.subscriptions = {}

    async def launch(self, skill):
        for inpt in skill.inputs:
            key = (skill, inpt.name)
            self.broker.create_channel(key)
            self.subscriptions[key] = self.broker.subscribe(channel_key=key)
            self._setup_watcher(skill, inpt.name)

        for outpt in skill.outputs:
            key = (skill, outpt.name)
            self.broker.create_channel(key)
            self._setup_provider(skill, outpt.name)

        skill.io = Facade(self, skill)
        await self.scheduler.spawn(skill)

    def _setup_provider(self, skill, key, channel=None):
        func = skill._provides[key]
        self.broker.register_provider(
            channel or (skill, key), self._request_output, function=func, skill=skill
        )

    def _setup_watcher(self, skill, key):
        if len(skill._watching.get(key, [])) > 0:
            self.broker.add_callback(
                channel_key=(skill, key), callback=self._trigger_watching
            )

    async def _trigger_watching(self, channel, _):
        skill, key = channel
        for function in skill._watching.get(key, []):
            await self._request_output(skill=skill, function=function)

    async def _request_output(self, *, skill, function):
        result = await self.scheduler.step(skill, function)
        for k, i in result.items():
            await self.broker.publish((skill, k), i)

    async def abort(self, skill):
        await self.scheduler.halt(skill)

    async def pull_skill_input(self, skill, key):
        sub = self.subscriptions[(skill, key)]
        return await self.broker.receive((skill, key), sub)

    async def push_skill_input(self, skill, key, value):
        await self.broker.publish(channel_key=(skill, key), message=value)

    async def pull_skill_output(self, skill, key):
        return await self.broker.receive(channel_key=(skill, key))

    def connect(self, output_skill, output_key, input_skill, input_key):
        # Use provider for the second skill to use the first skill
        self._setup_provider(output_skill, output_key, channel=(input_skill, input_key))

        # When the first skill produces output, publish into channel for second skill.
        async def passthru(_, message):
            await self.broker.publish(
                channel_key=(input_skill, input_key), message=message
            )

        # Connect the output of first skill to the callback publishing to second skill.
        self.broker.add_callback(
            channel_key=(output_skill, output_key), callback=passthru
        )

    async def shutdown(self):
        await self.scheduler.shutdown()
        await self.broker.shutdown()
