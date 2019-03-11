# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

from .types import create_type


class Variable:
    """Base class that describes a `Skill` input or output.
    """

    def __init__(self, name: str, *, spec: str, desc: str = ""):
        self.name = name
        self.spec = spec
        self.desc = desc

        self.type = create_type(spec)

    def as_dict(self):
        return {k: v for k, v in self.__dict__.items() if k not in ["type"]}


class SkillOutput(Variable):
    """Schema describing a single output of a `Skill`.
    """


class SkillInput(Variable):
    """Schema describing a single input of a `Skill`.
    """

    def __init__(self, name: str, *, spec: str, defaults: list = [], desc: str = ""):
        super(SkillInput, self).__init__(name=name, spec=spec, desc=desc)
        self.defaults = defaults


class SkillSchema:
    """Schema that describes a complete `Skill`.
    """

    def __init__(self, uri, *, inputs, outputs):
        self.uri = uri
        self.inputs = inputs
        self.outputs = outputs

    def as_dict(self):
        return dict(
            uri=self.uri,
            inputs=[i.as_dict() for i in self.inputs],
            outputs=[o.as_dict() for o in self.outputs],
        )
