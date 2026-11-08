"""Thin native adapter loading only its exact adjacent implementation."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_spec = spec_from_file_location("parametric_630d6cc550e4", _path)
_prototype = module_from_spec(_spec)
_spec.loader.exec_module(_prototype)

program = _prototype.program
generate = _prototype.generate
