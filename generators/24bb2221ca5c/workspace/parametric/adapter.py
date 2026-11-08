"""Native promotion entrypoint with exact task-local imports."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent


def _load(name: str):
    path = HERE / name
    module_name = "_24bb_parametric_" + path.stem + "_" + hashlib.sha256(
        str(path).encode()
    ).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load task-local module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_RULES = _load("rules.py")


def program(settings):
    return _RULES.program(settings)


def generate(seed, settings, demos, queries):
    return _load("prototype.py").generate(seed, settings, demos, queries)
