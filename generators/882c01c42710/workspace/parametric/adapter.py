"""Native opt-in adapter for the 882c01c42710 parametric family."""
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_parametric_882c01c42710", _path)
_implementation = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_implementation)


def program(settings):
    return _implementation.program(settings)


def generate(seed, settings, demos, queries):
    return _implementation.generate(seed, settings, demos, queries)
