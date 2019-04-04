# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import pytest
import random
import asyncio

import aiohttp, aiohttp.web, aiohttp.test_utils

from genlib.web.server import Server


# All the tests in this file can be treated as asynchronous.
pytestmark = pytest.mark.asyncio


class FakeSession:
    def __init__(self, websock):
        self.websock = websock
        self.messages = []

    async def run(self):
        async for msg in self.websock:
            cmd = msg.json()
            if cmd == "assert":
                assert False
            if cmd == "break":
                break


@pytest.fixture()
async def server():
    server = Server(make_session=FakeSession)

    runner = aiohttp.test_utils.TestServer(server, host="127.0.0.1")
    await runner.start_server()

    server.url = f"http://{runner.host}:{runner.port}"
    yield server

    await runner.close()


@pytest.fixture()
async def client():
    async with aiohttp.ClientSession() as client:
        yield client


class TestServerSingleClient:
    async def test_ignore_unknown(self, server, client):
        async with client.ws_connect(server.url) as conn:
            assert len(server.sessions) == 1
            await conn.send_json("unknown")
            assert len(server.sessions) == 1

    async def test_client_disconnect(self, server, client):
        async with client.ws_connect(server.url) as conn:
            assert len(server.sessions) == 1
            await conn.close()
            assert len(server.sessions) == 0

    async def test_clean_shutdown(self, server, client):
        async with client.ws_connect(server.url) as conn:
            assert len(server.sessions) == 1
            await conn.send_json("assert")
            await asyncio.sleep(0.01)
            assert len(server.sessions) == 0


class TestServerUnderLoad:
    async def _run_client(self, url):
        client = aiohttp.ClientSession()
        try:
            async with client.ws_connect(url) as conn:
                while not conn.closed:
                    cmd = random.choice(["close", "unknown", "assert", "break"])
                    if cmd == "close":
                        await conn.close()
                    else:
                        await conn.send_json(cmd)
        finally:
            await client.close()

    async def test_thousand_connections(self, server):
        tasks = [asyncio.create_task(self._run_client(server.url)) for _ in range(1000)]
        await asyncio.wait(tasks)

        assert len(server.sessions) == 0
