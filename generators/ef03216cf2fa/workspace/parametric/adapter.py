"""Native promotion entry point; load only the adjacent exact source path."""
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_ef03216cf2fa_edge_prototype", _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

program = _module.program
generate = _module.generate
