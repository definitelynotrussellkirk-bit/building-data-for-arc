"""Native promotion adapter for the task-local tie-order prototype."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys


def _prototype():
    path = Path(__file__).resolve().with_name("prototype.py")
    name = "_a55c1997c5e3_parametric_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    cached = sys.modules.get(name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load adjacent prototype: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def program(settings):
    return _prototype().rule_source(settings)


def generate(seed, settings, demos, queries):
    return _prototype().generate_episode(seed, settings, demos, queries)
