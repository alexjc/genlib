# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

from genlib.core.stream import Item


class Recipe:
    """Instructions to instanciate and configure a `Skill`.
    """

    def __init__(self, schema: "Schema", parameters: "Dict[Item]"):
        self.schema = schema
        self.parameters = {k: Item(v) for k, v in parameters.items()}

        inputs = {i.name for i in self.schema.inputs}
        self.unspecified = inputs - set(parameters.keys())

    def is_unspecified(self, input_name):
        return input_name in self.unspecified
