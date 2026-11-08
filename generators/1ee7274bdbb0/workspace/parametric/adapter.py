"""Load this task's adjacent native implementation by its exact path."""
import importlib.util
from pathlib import Path

_path = Path(__file__).with_name("native_family.py")
_spec = importlib.util.spec_from_file_location("arcpuzzles_tiles_1ee7274bdbb0_native", _path)
_native = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_native)
program = _native.program
generate = _native.generate
