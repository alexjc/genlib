# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import asyncio
import aiohttp.web

from .session import UserSession
from ..actor import Actor
from ..registry import LocalRegistry


class Server(aiohttp.web.Application):
    def __init__(self):
        super(Server, self).__init__()
        self.registry = LocalRegistry()
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
        except asyncio.CancelledError:
            pass
        finally:
            self.sessions.remove(session)
            await session.shutdown()

        if not websock.closed:
            await websock.close()
        return websock

    def make_session(self, *args, **kwargs):
        return UserSession(*args, **kwargs)
