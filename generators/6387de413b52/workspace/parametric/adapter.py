"""Exact-path native adapter for the 6387de413b52 axis-role family."""
import hashlib
import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_axis_roles_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
_IMPL = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_IMPL)

program = _IMPL.program
generate = _IMPL.generate
predict = _IMPL.predict
intermediate = _IMPL.intermediate
paint_intermediate = _IMPL.paint_intermediate
public_view = _IMPL.public_view
