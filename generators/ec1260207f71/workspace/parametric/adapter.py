"""Native promotion entry points; load only this adjacent prototype."""
from pathlib import Path
import importlib.util

_path = Path(__file__).resolve().with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_ec1260207f71_row_transfer", _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
program = _module.program
generate = _module.generate
