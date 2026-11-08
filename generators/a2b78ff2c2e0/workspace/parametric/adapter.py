"""Load this family's exact adjacent implementation."""
import importlib.util
from pathlib import Path

_path = Path(__file__).with_name("native_family.py")
_spec = importlib.util.spec_from_file_location("native_a2b78ff2c2e0", _path)
_native = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_native)
program = _native.program
generate = _native.generate
