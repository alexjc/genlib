# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import uuid
import aiohttp.web


class Client:
    def __init__(self, url):
        self.url = url
        self.session = None
        self.connection = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        try:
            self.connection = await self.session.ws_connect(self.url)
        except:
            await self.session.close()
            raise
        return self

    async def __aexit__(self, *exc_info):
        await self.connection.close()
        await self.session.close()
        self.session = None

    async def get_listing(self):
        await self.connection.send_json({"type": "listing"})
        return await self.connection.receive_json()

    async def invoke(self, command, parameters=None):
        msg = {
            "type": "invoke",
            "command": command,
            "parameters": parameters or {},
            "uuid": uuid.uuid1().hex,
        }
        await self.connection.send_json(msg)
        return await self.connection.receive_json()

    async def revoke(self, skill):
        await self.connection.send_json({"type": "revoke", "uuid": skill["uuid"]})

    async def push_input(self, skill, key, value):
        msg = {"type": "push_input", "uuid": skill["uuid"], "data": {key: value}}
        await self.connection.send_json(msg)

    async def pull_output(self, skill, key):
        msg = {"type": "pull_output", "uuid": skill["uuid"], "key": key}
        await self.connection.send_json(msg)
        return await self.connection.receive_json()
