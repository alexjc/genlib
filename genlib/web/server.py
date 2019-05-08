# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import asyncio
import aiohttp.web

from .session import UserSession
from ..runtime.actor import Actor
from ..runtime.registry import LocalRegistry


class Server(aiohttp.web.Application):
    def __init__(self, registry=None):
        super(Server, self).__init__()
        self.registry = registry or LocalRegistry()
        self.listing = {}
        self.sessions = []

        self.setup_routes()

    def setup_routes(self):
        self.router.add_get("/io", self.serve_session)

    def load_skills(self, folder, watch=True):
        self.registry.load_folder(folder, watch)

    def expose_skill(self, alias, uri):
        self.listing[alias] = uri

    async def serve_session(self, request):
        websock = aiohttp.web.WebSocketResponse()
        await websock.prepare(request)

        actor = Actor(self.registry, self.listing)
        session = self.make_session(websock, actor)
        try:
            self.sessions.append(session)
            await session.run()
        finally:
            await session.shutdown()
            self.sessions.remove(session)

        return websock

    async def shutdown(self):
        async def close(session):
            await session.shutdown()
            await session.websock.close(
                code=aiohttp.WSCloseCode.GOING_AWAY, message="Server Shutdown"
            )

        if len(self.sessions) > 0:
            await asyncio.wait([close(session) for session in self.sessions])
        assert len(self.sessions) == 0

    def make_session(self, *args, **kwargs):
        return UserSession(*args, **kwargs)
