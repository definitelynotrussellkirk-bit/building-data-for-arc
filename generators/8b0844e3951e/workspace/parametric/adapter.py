"""Native adapter; load the exact adjacent implementation without module-cache reuse."""
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_modal_row_8b0844e3951e", _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

program = _module.program
generate = _module.generate
