"""Thin native adapter for the exact adjacent completion-route prototype."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_spec = spec_from_file_location("parametric_6d678fbbe87e", _path)
_prototype = module_from_spec(_spec)
_spec.loader.exec_module(_prototype)

program = _prototype.program
generate = _prototype.generate
sample_input = _prototype.sample_input
transform = _prototype.transform
completion_analysis = _prototype.completion_analysis
