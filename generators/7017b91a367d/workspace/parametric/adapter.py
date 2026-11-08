"""Native adapter loading only the adjacent overlap-policy implementation."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_path = Path(__file__).with_name("prototype.py")
_spec = spec_from_file_location("_overlap_policy_parametric", _path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"cannot load adjacent prototype: {_path}")
_module = module_from_spec(_spec)
_spec.loader.exec_module(_module)
program = _module.program
generate = _module.generate
