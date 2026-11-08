"""Native interface; load only the adjacent implementation, never a cached name."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_path = Path(__file__).with_name("prototype.py")
_spec = spec_from_file_location("e46c2557ad08_parametric_prototype", _path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot load adjacent prototype: {_path}")
_prototype = module_from_spec(_spec)
_spec.loader.exec_module(_prototype)

program = _prototype.program
generate = _prototype.generate
