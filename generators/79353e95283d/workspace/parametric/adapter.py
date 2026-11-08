"""Thin native promotion adapter, loading only its exact adjacent implementation."""
from pathlib import Path
import hashlib
import importlib.util
import sys

_path = Path(__file__).resolve().with_name("native.py")
_name = "_panels_native_" + hashlib.sha256(str(_path).encode()).hexdigest()
if _name not in sys.modules:
    _spec = importlib.util.spec_from_file_location(_name, _path)
    _module = importlib.util.module_from_spec(_spec)
    sys.modules[_name] = _module
    _spec.loader.exec_module(_module)
else:
    _module = sys.modules[_name]

program = _module.program
generate = _module.generate
