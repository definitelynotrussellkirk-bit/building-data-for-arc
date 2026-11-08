"""Native promotion entrypoints; load only the adjacent exact implementation."""
from pathlib import Path
import hashlib
import importlib.util
import sys
_path = Path(__file__).resolve().with_name('union_family.py')
_name = '_stamp_region_' + hashlib.sha256(str(_path).encode()).hexdigest()[:16]
_spec = importlib.util.spec_from_file_location(_name, _path)
_module = importlib.util.module_from_spec(_spec)
sys.modules[_name] = _module
_spec.loader.exec_module(_module)
program = _module.program
generate = _module.generate
