# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import pytest
import asyncio
import logging

import aiohttp

from genlib.actor import Actor
from genlib.web.session import UserSession


# All the tests in this file can be treated as asynchronous.
pytestmark = pytest.mark.asyncio


@pytest.fixture()
async def session(caplog, mocker):
    messages = asyncio.Queue()

    class MockWebSocket:
        async def __aiter__(self):
            while True:
                yield await messages.get()

        async def send_json(self, data):
            self.data = data

    session = UserSession(websock=MockWebSocket(), actor=mocker.Mock(Actor))
    caplog.set_level(logging.ERROR, logger="genlib.session")

    session._messages = messages
    session._task = asyncio.create_task(session.run())

    yield session

    assert len(caplog.messages) == 0
    session._task.cancel()


@pytest.fixture()
async def registry():
    class MockRegistry:
        def list_skills_schema(self):
            return []

    yield MockRegistry()


class TestSession:
    async def _put_message(self, session, message):
        msg = aiohttp.WSMessage(aiohttp.web.WSMsgType.TEXT, data=message, extra="")
        await session._messages.put(msg)
        await asyncio.sleep(0.001)

    async def test_close_message(self, session):
        msg = aiohttp.WSMessage(aiohttp.web.WSMsgType.CLOSE, data={}, extra="")
        await session._messages.put(msg)
        await asyncio.sleep(0.001)
        assert session._task.done()

    async def test_unknown_message(self, session, caplog):
        caplog.set_level(logging.WARNING, logger="genlib.session")
        await self._put_message(session, '{"type": "custom"}')

        assert len(caplog.records) == 1
        assert "Websocket message of type `custom` unknown." in caplog.text
        assert not session._task.done()

    async def test_log_exception(self, session, caplog):
        caplog.set_level(logging.ERROR, logger="genlib.session")
        await self._put_message(session, '{"type": "invoke"}')

        assert len(caplog.records) == 1
        assert "Failed to handle request of type `invoke`." in caplog.text
        assert not session._task.done()

    async def test_listing(self, session):
        session.actor.get_listing.return_value = ["A", "B", "C"]
        await self._put_message(session, '{"type": "listing"}')
        await asyncio.sleep(0.001)

        assert session.websock.data == {"data": ["A", "B", "C"], "type": "listing"}
        assert not session._task.done()

    async def test_connect(self, session):
        await self._put_message(session, '{"type": "connect"}')
