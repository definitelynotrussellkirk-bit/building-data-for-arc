"""Load the adjacent ba9d8eb0cd5a native family."""
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("family.py")
_spec = importlib.util.spec_from_file_location("native_parametric_ba9d8eb0cd5a", _path)
_family = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_family)
program = _family.program
generate = _family.generate
