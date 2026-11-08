"""Native entry points bound to the adjacent prototype by exact source path."""
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_pivot_color_38200022d1b7", _path)
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)

program = _prototype.program
generate = _prototype.generate
