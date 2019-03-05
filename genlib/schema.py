# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

from .types import create_type


class Output:
    def __init__(self, name: str, *, spec: str, desc: str = ""):
        self.name = name
        self.type = create_type(spec)
        self.desc = desc


class Input:
    def __init__(self, name: str, *, spec: str, defaults: list = [], desc: str = ""):
        self.name = name
        self.type = create_type(spec)
        self.defaults = defaults
        self.desc = desc
