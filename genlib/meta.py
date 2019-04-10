# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import inspect

CONFIG_ATTRIBUTE = "_genlib"


class SkillConfigurator(type):
    """Meta-class for skills to provide syntactic shorthands, validate the API
    implementation, and configure defaults.
    """

    def __new__(cls, clsname, superclasses, attributes):
        if len(superclasses) > 0:
            cls.check_parameters(cls, attributes)
            cls.setup_provides(cls, attributes)
            cls.setup_watching(cls, attributes)
        return type.__new__(cls, clsname, superclasses, attributes)

    def check_parameters(cls, attributes):
        inputs = attributes.get("inputs", [])
        outputs = attributes.get("outputs", [])
        assert len(outputs) > 0, "No outputs declared."
        assert len({i.name for i in inputs} & {o.name for o in outputs}) == 0

    def setup_provides(cls, attributes: dict):
        provides_map = {}
        functions = [f for f in attributes.values() if is_method(f)]

        for obj in functions:
            config = getattr(obj, CONFIG_ATTRIBUTE, {})
            for key in config.get("provides", []):
                assert key not in provides_map
                provides_map[key] = obj

        found = set(provides_map.keys())
        outputs = {o.name for o in attributes.get("outputs", [])}
        for key in outputs - found:
            assert len(functions) > 0, f"No class methods found for {key}."
            assert len(functions) == 1, f"Ambiguous method for providing {key}."
            provides_map[key] = functions[0]
        attributes["_provides"] = provides_map

    def setup_watching(cls, attributes: dict):
        watching_map = {}
        for obj in [f for f in attributes.values() if is_method(f)]:
            config = getattr(obj, CONFIG_ATTRIBUTE, {})
            for key in config.get("watching", []):
                watching_map.setdefault(key, [])
                watching_map[key].append(obj)
        attributes["_watching"] = watching_map


def is_method(obj):
    def is_special(name):
        return any(name.startswith(p) for p in {"on_", "_"})

    return inspect.isfunction(obj) and not is_special(obj.__name__)


def watching(*inputs):
    def decorate(function):
        config = vars(function).setdefault(CONFIG_ATTRIBUTE, {})
        assert "watching" not in config
        config["watching"] = inputs
        return function

    return decorate


def provides(*outputs):
    def decorate(function):
        config = vars(function).setdefault(CONFIG_ATTRIBUTE, {})
        assert "provides" not in config
        config["provides"] = outputs
        return function

    return decorate
