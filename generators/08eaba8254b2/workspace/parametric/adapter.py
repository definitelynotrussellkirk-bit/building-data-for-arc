"""Native promotion adapter loading its adjacent implementation by exact path."""
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_stacked_xor_parametric_impl", _path)
_impl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_impl)


def program(settings):
    return _impl.program(settings)


def generate(seed, settings, demos, queries):
    return _impl.generate(seed, settings, demos, queries)

_UNION_PATH = Path(__file__).resolve().with_name("union.py")
_UNION_SPEC = importlib.util.spec_from_file_location("_union_08eaba8254b2", _UNION_PATH)
_UNION = importlib.util.module_from_spec(_UNION_SPEC)
_UNION_SPEC.loader.exec_module(_UNION)
program = _UNION.program
generate = _UNION.generate
