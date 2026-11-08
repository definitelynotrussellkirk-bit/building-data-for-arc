"""Native adapter; load the adjacent family by exact path, never cached name."""
import hashlib
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("family.py")
_spec = importlib.util.spec_from_file_location("_frame_family_" + hashlib.sha256(str(_path).encode()).hexdigest(), _path)
_family = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_family)

program = _family.program
generate = _family.generate

