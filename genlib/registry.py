# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import os
import sys
import hashlib
import inspect
import importlib.util

import watchdog.events
import watchdog.observers

from . import skills


__all__ = ["LocalRegistry", "FileSystemWatcher"]


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
        self.watcher = FileSystemWatcher(callback=self.load_file)

    def load_folder(self, path, watch=True):
        if watch:
            self.watcher.monitor(path)

        self._create_package(path)

        for filename in self._walk_folder(path, is_python_source):
            self.load_file(path, filename)

    def _create_package(self, path):
        package_name = hashlib.md5(path.encode("utf-8")).hexdigest()
        package_spec = importlib.util.spec_from_file_location(
            package_name, path + "/__init__.py", submodule_search_locations=[path]
        )
        package_obj = importlib.util.module_from_spec(package_spec)
        sys.modules[package_name] = package_obj

    def load_file(self, root, path):
        package_name = hashlib.md5(root.encode("utf-8")).hexdigest()
        module_name = os.path.splitext(path[len(root) + 1 :])[0].replace("/", ".")
        module_name = package_name + "." + module_name
        module_obj = self._import_file(module_name, path)
        self.load_objects(module_obj, path)

    def load_objects(self, module, path):
        for key in dir(module):
            obj = getattr(module, key)
            if not is_python_skill(obj):
                continue
            self.skills[f"{path}:{key}"] = obj

    def _import_file(self, name, path):
        module_spec = importlib.util.spec_from_file_location(name, path)
        module_obj = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module_obj)
        self.modules[path] = module_obj
        return module_obj

    def _walk_folder(self, path, predicate):
        for root, _, files in os.walk(path):
            for f in files:
                filename = os.path.join(root, f)
                if predicate(filename):
                    yield filename


class FileSystemWatcher:
    """Monitoring thread that captures file-system events in specified folders.
    """

    def __init__(self, callback):
        self.callback = callback
        self.observers = {}
        self.thread = watchdog.observers.Observer()
        self.thread.start()

    def shutdown(self):
        self.thread.stop()
        self.thread.join()

    def monitor(self, root):
        observer = FolderObserver(lambda path: self.callback(root, path))
        self.observers[root] = observer
        self.thread.schedule(observer, root, recursive=True)


class FolderObserver(watchdog.events.FileSystemEventHandler):
    """Handles file-system callbacks for a specific folder on disk.
    """

    def __init__(self, callback):
        super(FolderObserver, self).__init__()
        self.callback = callback

    def on_modified(self, event):
        if not event.is_directory and is_python_source(event.src_path):
            self.callback(event.src_path)
