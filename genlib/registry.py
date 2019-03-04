# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import os
import inspect

from . import skills


__all__ = ["LocalRegistry"]


def is_skill(obj):
    return (
        inspect.isclass(obj)
        and issubclass(obj, skills.BaseSkill)
        and obj not in skills.__dict__.values()
    )


def is_python_source(path):
    return path.endswith(".py")


class LocalRegistry(object):
    """Loads and stores skills from file-system, indexing them by URI.
    """

    def __init__(self):
        self.cache = {}
        self.skills = {}

    def load_folder(self, path):
        for filename in self._walk_folder(path, is_python_source):
            self.load_file(filename)

    def load_file(self, path):
        module = self._compile_file(path)

        for key, obj in module.items():
            if not is_skill(obj):
                continue

            self.skills[f"{path}:{key}"] = obj

    def _compile_file(self, path):
        with open(path, "r", encoding="utf-8") as source:
            module_code = compile(source.read(), path, "exec")

        module_name = os.path.splitext(path)[0].replace("/", ".")
        module_dict = {"__file__": path, "__name__": module_name}
        exec(module_code, module_dict)  # pylint: disable=exec-used
        self.cache[path] = module_dict
        return module_dict

    def _walk_folder(self, path, predicate):
        for root, _, files in os.walk(path):
            for f in files:
                filename = os.path.join(root, f)
                if predicate(filename):
                    yield filename
