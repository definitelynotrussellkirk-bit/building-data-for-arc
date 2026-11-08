"""Exact-adjacent native adapter for the seeded-frame scope family."""
import hashlib
import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().with_name("native.py")
_SPEC = importlib.util.spec_from_file_location(
    "_seeded_frame_native_" + hashlib.sha256(str(_PATH).encode()).hexdigest(), _PATH
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load {_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
program = _MODULE.program
generate = _MODULE.generate
