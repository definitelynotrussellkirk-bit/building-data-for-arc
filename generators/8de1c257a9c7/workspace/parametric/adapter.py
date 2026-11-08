"""Thin native adapter for the existing task-local stamp-transform prototype."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

_path = Path(__file__).resolve().with_name("prototype.py")
_spec = spec_from_file_location("_native_stamp_transform_8de1c257a9c7", _path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot load stamp-transform prototype at {_path}")
_prototype = module_from_spec(_spec)
sys.modules[_spec.name] = _prototype
_spec.loader.exec_module(_prototype)


def program(settings=None):
    return _prototype.program(settings)


def generate(seed, settings=None, demos=3, queries=4):
    return _prototype.generate(seed, settings, demos, queries)
