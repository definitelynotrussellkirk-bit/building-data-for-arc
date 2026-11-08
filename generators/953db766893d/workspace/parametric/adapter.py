"""Native adapter for the matched minimum/maximum room-extreme family."""
import hashlib
import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location(
    "_room_extreme_" + hashlib.sha256(str(_PATH).encode()).hexdigest(), _PATH
)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
program = _MODULE.program
generate = _MODULE.generate
