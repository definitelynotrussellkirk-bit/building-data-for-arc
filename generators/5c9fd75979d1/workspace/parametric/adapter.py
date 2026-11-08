"""Native adapter; load this task's implementation by exact adjacent path."""
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_bbox_threshold_5c9fd75979d1", _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
program = _module.program
generate = _module.generate
