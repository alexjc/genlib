# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import asyncio

# Backwards compatibility with Python 3.6 for `current_task`.
if not hasattr(asyncio, "current_task"):
    asyncio.current_task = asyncio.Task.current_task

# Backwards compatibility with Python 3.6 for `create_task`.
if not hasattr(asyncio, "create_task"):
    asyncio.create_task = lambda t: asyncio.get_event_loop().create_task(t)
