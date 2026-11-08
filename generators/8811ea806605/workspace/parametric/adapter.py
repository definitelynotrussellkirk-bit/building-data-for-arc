"""Native promotion entry point, bound to this adjacent implementation."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_spec = spec_from_file_location("gravity_8811ea806605_parametric", _path)
_module = module_from_spec(_spec)
_spec.loader.exec_module(_module)

program = _module.program
generate = _module.generate
