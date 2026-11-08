"""Native adapter; resolve the adjacent implementation by its exact path."""
import hashlib
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_name = "_reflection_parametric_" + hashlib.sha256(str(_path).encode()).hexdigest()[:16]
_spec = importlib.util.spec_from_file_location(_name, _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
program = _module.program
generate = _module.generate
