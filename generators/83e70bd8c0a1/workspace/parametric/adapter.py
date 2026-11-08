"""Native promotion entry point bound to this task's adjacent implementation."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_spec = spec_from_file_location("anti_relay_83e70bd8c0a1_parametric", _path)
assert _spec is not None and _spec.loader is not None
_module = module_from_spec(_spec)
_spec.loader.exec_module(_module)

program = _module.program
generate = _module.generate
public_view = _module.public_view
