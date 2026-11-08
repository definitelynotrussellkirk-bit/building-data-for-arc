"""Native adapter; load this task's implementation by its exact adjacent path."""
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_parametric_1d26c382ab68", _path)
_impl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_impl)

program = _impl.program
generate = _impl.generate
expected_output = _impl.expected_output
rival_outputs = _impl.rival_outputs
teaching_check = _impl.teaching_check
model_view = _impl.model_view
analyze = _impl.analyze
counterfactual_program = _impl.counterfactual_program
