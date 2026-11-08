"""Native adapter for the keyed straight/clockwise-elbow route family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys


def _module():
    path = Path(__file__).with_name("family.py").resolve()
    name = "_route_7d09ccad28c8_" + hashlib.sha256(path.read_bytes()).hexdigest()
    cached = sys.modules.get(name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def program(settings):
    return _module().program(settings)


def generate(seed, settings, demos, queries):
    return _module().generate(seed, settings, demos, queries)


def __getattr__(name):
    if name in {
        "build_input",
        "route_analysis",
        "transform",
        "transform_wrong_intermediate",
        "validate_settings",
    }:
        return getattr(_module(), name)
    raise AttributeError(name)
