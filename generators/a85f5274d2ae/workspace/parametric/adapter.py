"""Native promotion entrypoint; load only the implementation beside this file."""
import hashlib
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("native.py")
_spec = importlib.util.spec_from_file_location(
    "_a85_native_" + hashlib.sha256(str(_path).encode()).hexdigest()[:12], _path)
_native = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_native)

program = _native.program
generate = _native.generate
