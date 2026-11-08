"""Native promotion entrypoint for the nearest/farthest marker family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _native():
    path = HERE / "native.py"
    source = path.read_bytes()
    name = "_9971_parametric_" + hashlib.sha256(str(path).encode() + source).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load task-local native family {path}")
    module = importlib.util.module_from_spec(spec)
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


def program(settings):
    return _native().program(settings)


def generate(seed, settings, demos, queries):
    return _native().generate(seed, settings, demos, queries)
