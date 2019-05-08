# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import unittest

from genlib.core.stream import Item


class TestStreamItem(unittest.TestCase):
    def test_unique_uuid(self):
        i1, i2 = Item(data=123), Item(data=456)
        assert i1.uuid != i2.uuid
