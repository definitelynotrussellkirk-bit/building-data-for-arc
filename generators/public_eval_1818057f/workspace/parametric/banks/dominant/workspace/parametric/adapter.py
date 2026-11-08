"""Exact-adjacent native adapter; avoids global module cache collisions."""
from pathlib import Path
import hashlib
import importlib.util
import sys

_path = Path(__file__).with_name('prototype.py')
_name = '_plus_' + hashlib.sha256(str(_path.resolve()).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
impl = importlib.util.module_from_spec(_spec)
sys.modules[_name] = impl
assert _spec.loader is not None
_spec.loader.exec_module(impl)
program = impl.program
generate = impl.generate
