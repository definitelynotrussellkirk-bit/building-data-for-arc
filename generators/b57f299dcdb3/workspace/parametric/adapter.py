"""Native promotion adapter; the adjacent module is loaded by exact path."""
import hashlib
import importlib.util
from pathlib import Path
import sys

_path = Path(__file__).with_name('prototype.py').resolve()
_name = '_plus_census_' + hashlib.sha256(str(_path).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
_prototype = importlib.util.module_from_spec(_spec)
sys.modules[_name] = _prototype
_spec.loader.exec_module(_prototype)
program = _prototype.program
generate = _prototype.generate
solve_python = _prototype.solve_python
