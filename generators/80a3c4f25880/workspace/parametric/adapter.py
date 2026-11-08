"""Native adapter, loading adjacent source by exact path, not a cached basename."""
import hashlib
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_name = "_rotation_selector_" + hashlib.sha256(str(_path).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)

program = _prototype.program
generate = _prototype.generate
