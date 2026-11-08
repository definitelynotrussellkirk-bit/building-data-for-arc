"""Load the exact adjacent cue-axis family implementation."""
import hashlib
import importlib.util
from pathlib import Path
import sys

_path = Path(__file__).with_name("family.py")
_name = "_a6294f07bff6_parametric_" + hashlib.sha256(_path.read_bytes()).hexdigest()[:16]
_spec = importlib.util.spec_from_file_location(_name, _path)
if _spec is None or _spec.loader is None:
    raise ImportError(_path)
_family = importlib.util.module_from_spec(_spec)
sys.modules[_name] = _family
_spec.loader.exec_module(_family)
program = _family.program
generate = _family.generate
