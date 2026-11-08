"""Native API adapter; load this task's exact adjacent implementation."""
import importlib.util
import hashlib
from pathlib import Path

_path = Path(__file__).with_name("prototype.py").resolve()
_name = "_area_merge_" + hashlib.sha256(str(_path).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)

program = _prototype.program
generate = _prototype.generate
