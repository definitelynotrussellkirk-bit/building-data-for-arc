"""Native adapter; load adjacent authored source by exact path and content."""
import hashlib
import importlib.util
from pathlib import Path
import sys

_path = Path(__file__).resolve().with_name("prototype.py")
_body = _path.read_bytes()
_name = "_hole_threshold_" + hashlib.sha256(str(_path).encode() + _body).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
_module = importlib.util.module_from_spec(_spec)
sys.modules[_name] = _module
exec(compile(_body, str(_path), "exec"), _module.__dict__)

program = _module.program
generate = _module.generate
