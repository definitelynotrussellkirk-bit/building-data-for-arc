"""Native promotion adapter; bind the adjacent prototype by exact path."""
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_transform_application_adapter_impl", _path)
_impl = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_impl)


def program(settings):
    return _impl.program(settings)


def generate(seed, settings, demos, queries):
    return _impl.generate(seed, settings, demos, queries)
