"""Exact-path native adapter for the retained rotation prototype and extension."""
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("native.py")
_spec = importlib.util.spec_from_file_location("_native_l_rotation", _path)
_native = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_native)

program = _native.program
generate = _native.generate
model_view = _native.model_view
analyze = _native.analyze
transform = _native.transform
teaching_check = _native.teaching_check
counterfactual_program = _native.counterfactual_program
