# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import typing


__all__ = ["add_type_class", "check_type", "create_type"]


TYPE_REGISTRY = {
    "T": typing.T,
    "List": typing.List,
    "Dict": typing.Dict,
    "Any": typing.Any,
}


def add_type_class(name, type_class):
    TYPE_REGISTRY[name] = type_class


def create_type(spec):
    try:
        assert isinstance(spec, str), "Expected type specification to be a string."
        return eval(spec, TYPE_REGISTRY)  # pylint: disable=eval-used
    except Exception:  # pylint: disable=broad-except
        return None


def check_type(spec):
    return create_type(spec) is not None
