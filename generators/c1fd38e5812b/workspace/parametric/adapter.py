"""Thin native adapter loading this task's implementation by exact path."""
import importlib.util
from pathlib import Path

_path = Path(__file__).with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_c1fd38e5812b_native_prototype", _path)
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)

program = _prototype.program
generate = _prototype.generate
