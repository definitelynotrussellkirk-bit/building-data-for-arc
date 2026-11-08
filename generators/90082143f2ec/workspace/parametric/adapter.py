"""Native root adapter over the retained axis-policy Racket materializer."""
import hashlib
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("native.py")
_spec = importlib.util.spec_from_file_location("_native_axis_" + hashlib.sha256(str(_path).encode()).hexdigest(), _path)
_native = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_native)

program = _native.program
generate = _native.generate
solve = _native.solve
observables = _native.observables
visible_turn = _native.visible_turn
teaching_report = _native.teaching_report
rival_names = _native.rival_names
rival_output = _native.rival_output
write_batch = _native.write_batch
