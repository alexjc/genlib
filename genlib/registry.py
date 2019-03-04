# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import os
import types
import inspect
import importlib

import reloader
import watchdog.events, watchdog.observers

from . import skills


__all__ = ["LocalRegistry"]


def is_python_skill(obj):
    return (
        inspect.isclass(obj)
        and issubclass(obj, skills.BaseSkill)
        and obj not in skills.__dict__.values()
    )


def is_python_source(path):
    return path.endswith(".py")


class LocalRegistry:
    """Loads and stores skills from file-system, indexing them by URI.
    """

    def __init__(self):
        self.modules = {}
        self.skills = {}
        self.watcher = FolderWatcher(callback=self.reload_file)

    def load_folder(self, path, watch=True):
        if watch:
            self.watcher.monitor(path)

        for filename in self._walk_folder(path, is_python_source):
            self.load_file(filename)

    def load_file(self, path):
        module = self._import_file(path)

        for key in dir(module):
            obj = getattr(module, key)
            if not is_python_skill(obj):
                continue

            self.skills[f"{path}:{key}"] = obj

    def reload_file(self, path):
        print("Reloading...", path)
        reloader.reload(self.modules[path])

    def _import_file(self, path):
        module_name = os.path.splitext(path)[0].replace("/", ".")
        module_obj = importlib.import_module(module_name)
        self.modules[path] = module_obj
        return module_obj

    def _walk_folder(self, path, predicate):
        for root, _, files in os.walk(path):
            for f in files:
                filename = os.path.join(root, f)
                if predicate(filename):
                    yield filename


class FolderWatcher(watchdog.events.FileSystemEventHandler):
    """Monitoring thread that captures file-system events in specified folders.
    """

    def __init__(self, callback):
        super(FolderWatcher, self).__init__()
        self.callback = callback
        self.observer = watchdog.observers.Observer()
        self.observer.start()

    def monitor(self, path):
        self.observer.schedule(self, path, recursive=True)

    def on_modified(self, event):
        if not event.is_directory and is_python_source(event.src_path):
            self.callback(event.src_path)
