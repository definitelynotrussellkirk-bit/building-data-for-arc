"""Native adapter loaded from the exact adjacent prototype."""
import hashlib
import importlib.util
from pathlib import Path
import sys

_path = Path(__file__).resolve().with_name("prototype.py")
_name = "_elbow_order_" + hashlib.sha256(str(_path).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
_module = importlib.util.module_from_spec(_spec)
sys.modules[_name] = _module
_spec.loader.exec_module(_module)
program = _module.program
generate = _module.generate
