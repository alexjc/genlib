# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import asyncio
import logging

import aiohttp.web


class UserSession:
    def __init__(self, websock, actor):
        self.log = logging.getLogger("genlib.session")
        self.websock = websock
        self.actor = actor
        self.skills = {}
        self._tasks = []

    async def run(self):
        """Read messages from the client as they come in, and handle them in an
        asynchronous task to keep the websocket connection responsive.
        """
        async for msg in self.websock:
            if msg.type == aiohttp.web.WSMsgType.TEXT:
                task = asyncio.create_task(self._process(msg.json()))
                self._tasks.append(task)
            if msg.type == aiohttp.web.WSMsgType.CLOSE:
                break
        await asyncio.wait(self._tasks)

    async def shutdown(self):
        assert len(self._tasks) == 0
        await self.actor.shutdown()

    async def _process(self, msg: dict):
        """Process a websocket request by finding the appropriate message handler.
        """
        try:
            handler = getattr(self, "handle_" + msg["type"], self.handle_default)
            await handler(msg)
        except Exception:  # pylint: disable=broad-except
            self.log.exception("Failed to handle request of type `%s`.", msg["type"])
        finally:
            self._tasks.remove(asyncio.current_task())

    async def handle_listing(self, _: dict):
        listing = self.actor.get_listing()
        await self.websock.send_json({"type": "listing", "data": listing})

    async def handle_connect(self, msg: dict):
        pass

    async def handle_invoke(self, msg: dict):
        skill = await self.actor.invoke(msg["command"], msg.get("parameters", {}))
        self.skills[msg["uuid"]] = skill
        await self.websock.send_json({"type": "invoked", "uuid": msg["uuid"]})

    async def handle_revoke(self, msg: dict):
        skill = self.skills[msg["uuid"]]
        await self.actor.revoke(skill)

    async def handle_push_input(self, msg: dict):
        skill = self.skills[msg["uuid"]]
        for key, value in msg["data"].items():
            await self.actor.push_skill_input(skill, key, value)

    async def handle_pull_output(self, msg: dict):
        skill = self.skills[msg["uuid"]]
        output = await self.actor.pull_skill_output(skill, msg["key"])
        await self.websock.send_json(
            {"type": "pulled_output", "uuid": msg["uuid"], "data": output.data}
        )

    async def handle_default(self, msg: dict):
        self.log.warning("Websocket message of type `%s` unknown.", msg["type"])
