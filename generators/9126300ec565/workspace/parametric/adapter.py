"""Native adapter loading only its exact adjacent implementation."""
from pathlib import Path
import hashlib
import importlib.util
import sys

_path = Path(__file__).resolve().with_name("prototype.py")
_name = "_frame_axis_" + hashlib.sha256(str(_path).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
_impl = importlib.util.module_from_spec(_spec)
sys.modules[_name] = _impl
_spec.loader.exec_module(_impl)


def program(settings):
    return _impl.program(settings)


def generate(seed, settings, demos=3, queries=4):
    return _impl.generate(seed, settings, demos, queries)
