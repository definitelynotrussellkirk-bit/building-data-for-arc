"""Native adapter loading only the adjacent 6ecd8be24495 family."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_path = Path(__file__).with_name("family.py")
_spec = spec_from_file_location("_6ecd8be24495_parametric_family", _path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"cannot load adjacent family: {_path}")
_family = module_from_spec(_spec)
_spec.loader.exec_module(_family)

program = _family.program
generate = _family.generate
