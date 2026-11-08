"""Native adapter loading only the exact adjacent parametric prototype."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_native_270af96a99b0_" + hashlib.sha256(str(_PATH).encode()).hexdigest()


def _prototype():
    module = sys.modules.get(_NAME)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(_NAME, _PATH)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load adjacent 270af96a99b0 prototype")
    module = importlib.util.module_from_spec(spec)
    sys.modules[_NAME] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(_NAME, None)
        raise
    return module


def program(settings):
    return _prototype().program(settings)


def generate(seed, settings, demos=3, queries=4):
    return _prototype().generate(seed, settings, demos, queries)
