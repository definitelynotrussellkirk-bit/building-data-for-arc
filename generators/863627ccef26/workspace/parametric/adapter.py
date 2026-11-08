"""Native adapter loading the adjacent implementation by exact path."""
import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("_parametric_863627ccef26", _PATH)
_IMPL = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_IMPL)


def program(settings):
    return _IMPL.program(settings)


def generate(seed, settings, demos, queries):
    return _IMPL.generate(seed, settings, demos, queries)
