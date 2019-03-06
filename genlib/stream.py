# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import uuid


class Item:
    def __init__(self, data):
        self.uuid = uuid.uuid1()
        self.data = data
