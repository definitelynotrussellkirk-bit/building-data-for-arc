"""Native adapter for the proposed ray-tail turn-policy family."""
from pathlib import Path
import hashlib
import importlib.util

_PATH = Path(__file__).resolve().with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location(
    "_ray_turn_" + hashlib.sha256(str(_PATH).encode()).hexdigest(), _PATH
)
_MODULE = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_MODULE)
program = _MODULE.program
generate = _MODULE.generate
