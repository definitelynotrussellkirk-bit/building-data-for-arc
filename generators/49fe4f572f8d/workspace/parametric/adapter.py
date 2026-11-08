"""Native adapter loading only this task's adjacent implementation."""
import hashlib
import importlib.util
from pathlib import Path
import sys

_path = Path(__file__).resolve().with_name('prototype.py')
_name = '_49fe_gravity_' + hashlib.sha256(str(_path).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
prototype = importlib.util.module_from_spec(_spec)
sys.modules[_name] = prototype
_spec.loader.exec_module(prototype)
program = prototype.program
generate = prototype.generate
