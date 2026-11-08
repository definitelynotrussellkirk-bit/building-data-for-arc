"""Load the exact adjacent successive-reflection native implementation."""
import importlib.util
from pathlib import Path
_path = Path(__file__).with_name("native_family.py")
_spec = importlib.util.spec_from_file_location("native_abe8a3c35e86", _path)
_native = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_native)
program = _native.program
generate = _native.generate
