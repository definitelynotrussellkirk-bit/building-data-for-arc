"""Thin native adapter for the source-bound payload-axis translation family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys


def _family_module():
    path = Path(__file__).with_name("family.py").resolve()
    name = "_task_1a8932958b14_parametric_family_" + hashlib.sha256(
        str(path).encode("utf-8")
    ).hexdigest()
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load adjacent family source {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def program(settings):
    return _family_module().program(settings)


def generate(seed, settings, demos, queries):
    return _family_module().generate(seed, settings, demos, queries)
