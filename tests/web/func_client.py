# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import pytest
import random
import asyncio

import aiohttp, aiohttp.web, aiohttp.test_utils

from genlib.web.client import Client
from genlib.web.server import Server


# All the tests in this file can be treated as asynchronous.
pytestmark = pytest.mark.asyncio


from genlib.core.skills import Skill, Input, Output
from genlib.core.stream import Item


class DoEcho(Skill):

    inputs = [Input("ping", spec="int")]
    outputs = [Output("pong", spec="int")]

    async def process(self):
        ping_item, = await self.io.pull_inputs("ping")
        return {"pong": Item(ping_item.data)}


@pytest.fixture()
async def server():
    server = Server()
    server.registry._load_from_class("test.py:DoEcho", DoEcho)
    server.expose_skill("TestConnection", "test.py:DoEcho")

    runner = aiohttp.test_utils.TestServer(server, host="127.0.0.1")
    await runner.start_server()

    server.runner = runner
    server.url = f"ws://{runner.host}:{runner.port}/io"
    yield server

    await runner.close()
    assert len(server.sessions) == 0


class TestSingle:
    async def test_server_down(self, server):
        await server.runner.close()
        with pytest.raises(aiohttp.client_exceptions.ClientConnectorError):
            async with Client(server.url):
                pass

    async def test_connect_disconnect(self, server):
        async with Client(server.url):
            pass

    async def test_listing(self, server):
        async with Client(server.url) as client:
            listing = await client.get_listing()
            assert list(listing["data"].keys()) == ["TestConnection"]

    async def test_invoke_revoke(self, server):
        async with Client(server.url) as client:
            skill = await client.invoke("TestConnection")
            await client.revoke(skill)

    async def test_invoke_parameters(self, server):
        async with Client(server.url) as client:
            skill = await client.invoke("TestConnection", {"ping": 1001})
            msg = await client.pull_output(skill, "pong")
            assert msg["data"] == 1001
            await client.revoke(skill)

    async def test_push_pull(self, server):
        async with Client(server.url) as client:
            skill = await client.invoke("TestConnection")
            for i in range(10):
                await client.push_input(skill, "ping", i)
                msg = await client.pull_output(skill, "pong")
                assert msg["data"] == i
            await client.revoke(skill)


class TestMultiple:
    async def test_push_pull(self, server):
        run = TestSingle.test_push_pull
        tasks = [asyncio.create_task(run(self, server)) for _ in range(100)]
        await asyncio.wait(tasks)
