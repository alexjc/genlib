# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import os
import sys
import hashlib
import inspect
import importlib.util

import watchdog.events
import watchdog.observers

import genlib.skills
import genlib.schema

__all__ = ["LocalRegistry", "FileSystemWatcher"]


def is_python_skill(obj):
    return (
        inspect.isclass(obj)
        and issubclass(obj, genlib.skills.BaseSkill)
        and obj not in genlib.skills.__dict__.values()
    )


def is_python_source(path):
    return path.endswith(".py")


class LocalRegistry:
    """Loads and stores skills from file-system, indexing them by URI.
    """

    def __init__(self):
        self.modules = {}
        self.schemas = {}
        self.classes = {}
        self.watcher = FileSystemWatcher(callback=self._load_file)

    # ---------------------------------------------------------------------------------
    # Public Interface
    # ---------------------------------------------------------------------------------

    def load_folder(self, path, watch=True):
        if watch:
            self.watcher.monitor(path)

        self._create_package(path)

        for filename in self._walk_folder(path, is_python_source):
            self._load_file(path, filename)

    def construct(self, schema):
        return self.classes[schema.uri]()

    def find_skill_schema(self, uri):
        return self.schemas[uri]

    def list_skills_schema(self):
        return list(self.schemas.keys())

    # ---------------------------------------------------------------------------------
    # Helper Functions
    # ---------------------------------------------------------------------------------

    def _create_package(self, root):
        package_name = hashlib.md5(root.encode("utf-8")).hexdigest()
        package_spec = importlib.util.spec_from_file_location(
            package_name, root + "/__init__.py", submodule_search_locations=[root]
        )
        package_obj = importlib.util.module_from_spec(package_spec)
        sys.modules[package_name] = package_obj

    def _load_file(self, root, path):
        package_name = hashlib.md5(root.encode("utf-8")).hexdigest()
        module_path = path[len(root) + 1 :]
        module_name = os.path.splitext(module_path)[0].replace("/", ".")
        module_name = package_name + "." + module_name
        module_obj = self._import_file(module_name, path)
        self._load_objects(module_obj, module_path)

    def _load_objects(self, module, path):
        for key in dir(module):
            obj = getattr(module, key)
            if not is_python_skill(obj):
                continue
            uri = f"{path}:{key}"
            scm = genlib.schema.SkillSchema(uri, inputs=obj.inputs, outputs=obj.outputs)
            self.schemas[uri] = scm
            self.classes[uri] = obj

    def _import_file(self, name, path):
        module_spec = importlib.util.spec_from_file_location(name, path)
        module_obj = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module_obj)
        self.modules[path] = module_obj
        return module_obj

    def _walk_folder(self, path, predicate):
        for root, _, files in os.walk(path):
            for filename in files:
                full_path = os.path.join(root, filename)
                if predicate(full_path):
                    yield full_path


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
