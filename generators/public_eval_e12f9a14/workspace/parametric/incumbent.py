"""Source-bound adapter for public_eval_e12f9a14."""
from pathlib import Path
import hashlib
import importlib.util
import sys

_path = Path(__file__).with_name("prototype.py")
_name = "_ray_merge_e12f9a14_" + hashlib.sha256(str(_path.resolve()).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
impl = importlib.util.module_from_spec(_spec)
sys.modules[_name] = impl
_spec.loader.exec_module(impl)
program = impl.program
generate = impl.generate
