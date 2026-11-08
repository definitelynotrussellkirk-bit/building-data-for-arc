"""Native adapter loading only this task's adjacent implementation."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


_path = Path(__file__).resolve().with_name("prototype.py")
_spec = spec_from_file_location("parametric_ba0c6a5828f9_prototype", _path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"cannot load adjacent prototype: {_path}")
_prototype = module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def program(settings):
    return _prototype.program(settings)


def generate(seed, settings, demos=3, queries=4):
    return _prototype.generate(seed, settings, demos, queries)
