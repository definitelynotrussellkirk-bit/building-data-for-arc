"""Native promotion adapter; load the adjacent implementation by exact path."""
import importlib.util
from pathlib import Path
import sys

_path = Path(__file__).resolve().with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_7e03_center_cue_adapter_impl", _path)
_impl = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _impl
_spec.loader.exec_module(_impl)


def program(settings):
    return _impl.program(settings)


def generate(seed, settings, demos, queries):
    return _impl.generate(seed, settings, demos, queries)
