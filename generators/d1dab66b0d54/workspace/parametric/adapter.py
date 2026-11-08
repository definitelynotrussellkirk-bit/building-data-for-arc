"""Native adapter for the d1dab66b0d54 direction prototype."""
import importlib.util
from pathlib import Path

_path = Path(__file__).with_name("guide_shift.py")
_spec = importlib.util.spec_from_file_location("_d1dab66b0d54_guide_shift", _path)
_prototype = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_prototype)


def program(settings):
    return _prototype.program(settings)


def generate(seed, settings, demos, queries):
    return _prototype.generate(seed, settings, demos, queries)
