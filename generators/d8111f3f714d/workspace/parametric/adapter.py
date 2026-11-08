"""Native promotion adapter; import only this task's adjacent implementation."""
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("native_family.py")
_spec = importlib.util.spec_from_file_location("_d8111f3f714d_native_adapter", _path)
_family = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_family)


def program(settings=None):
    return _family.program(settings)


def generate(seed, settings=None, demos=3, queries=4):
    return _family.generate(seed, settings, demos, queries)
