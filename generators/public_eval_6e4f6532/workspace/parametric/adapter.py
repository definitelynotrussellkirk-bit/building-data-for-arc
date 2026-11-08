"""Same-home adapter for the native guide-directed relocation family."""
import importlib.util
from pathlib import Path
import sys

_path = Path(__file__).with_name("native_family.py")
_spec = importlib.util.spec_from_file_location("native_public_eval_6e4f6532", _path)
_native = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _native
_spec.loader.exec_module(_native)
program = _native.program
generate = _native.generate
