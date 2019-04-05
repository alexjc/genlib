# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import asyncio
import aiohttp.web

from .session import UserSession


class Server(aiohttp.web.Application):
    def __init__(self):
        super(Server, self).__init__()
        self.sessions = []
        self.router.add_get("/io", self.serve_session)

    async def serve_session(self, request):
        websock = aiohttp.web.WebSocketResponse()
        await websock.prepare(request)

        session = self.make_session(websock, interpreter=None, listing=None)
        try:
            self.sessions.append(session)
            await session.run()
        finally:
            self.sessions.remove(session)

        await websock.close()
        return websock

    def make_session(self, *args, **kwargs):
        return UserSession(*args, **kwargs)
