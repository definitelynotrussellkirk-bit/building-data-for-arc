"""Thin native adapter loading only the exact adjacent implementation."""
import hashlib
import importlib.util
from pathlib import Path
import sys

_path = Path(__file__).resolve().with_name("prototype.py")
_name = "_native_5d6fcce80b6a_" + hashlib.sha256(str(_path).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
_impl = importlib.util.module_from_spec(_spec)
sys.modules[_name] = _impl
assert _spec.loader is not None
_spec.loader.exec_module(_impl)

program = _impl.program
generate = _impl.generate
model_view = _impl.model_view
visible_turn = _impl.visible_turn
analyze = _impl.analyze
transform = _impl.transform
teaching_check = _impl.teaching_check
counterfactual_program = _impl.counterfactual_program
