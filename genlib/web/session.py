# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import asyncio
import logging

import aiohttp.web


class UserSession:
    def __init__(self, websock, registry):
        self.log = logging.getLogger("genlib.session")

        self.websock = websock
        self.registry = registry

    async def run(self):
        """Read messages from the client as they come in, and handle them in an
        asynchronous task to keep the websocket connection responsive.
        """
        async for msg in self.websock:
            if msg.type == aiohttp.web.WSMsgType.TEXT:
                asyncio.create_task(self._process(msg.json()))
            if msg.type == aiohttp.web.WSMsgType.CLOSE:
                break

    async def _process(self, msg: dict):
        """Process a websocket request by finding the appropriate message handler.
        """
        try:
            handler = getattr(self, "handle_" + msg["type"], self.handle_default)
            await handler(msg)
        except:
            self.log.exception(f"Failed to handle request of type `{msg['type']}`.")

    async def handle_listing(self, msg: dict):
        data = {
            uri: self.registry.find_skill_schema(uri).as_dict()
            for uri in self.registry.list_skills_schema()
        }
        await self.websock.send_json({"type": "listing", "data": data})

    async def handle_connect(self, msg: dict):
        pass

    async def handle_default(self, msg: dict):
        self.log.warning(f"Websocket message of type `{msg['type']}` unknown.")
