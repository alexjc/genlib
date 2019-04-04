# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import asyncio
import aiohttp.web


class Server(aiohttp.web.Application):
    def __init__(self, make_session):
        super(Server, self).__init__()
        self.sessions = []
        self.make_session = make_session
        self.router.add_get("/", self.serve_session)

    async def serve_session(self, request):
        websock = aiohttp.web.WebSocketResponse()
        await websock.prepare(request)

        session = self.make_session(websock)
        try:
            self.sessions.append(session)
            await session.run()
        finally:
            self.sessions.remove(session)

        await websock.close()
        return websock
