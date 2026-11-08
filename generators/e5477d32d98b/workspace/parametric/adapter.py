"""Native adapter for the task-local forward/reverse stencil family."""
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_e5477d32d98b_parametric_impl", _path)
_implementation = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_implementation)


def program(settings):
    return _implementation.program(settings)


def generate(seed, settings, demos, queries):
    return _implementation.generate(seed, settings, demos, queries)
