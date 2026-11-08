"""Native API loaded only from this task's exact adjacent family source."""
import hashlib
import importlib.util
from pathlib import Path
import sys

_path = Path(__file__).resolve().with_name("native_family.py")
_name = "_9000d0ea6484_family_" + hashlib.sha256(str(_path).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
_family = importlib.util.module_from_spec(_spec)
sys.modules[_name] = _family
_spec.loader.exec_module(_family)
program = _family.program
generate = _family.generate
apply_claim = _family.apply_claim
describe = _family.describe
public_turn = _family.public_turn
rivals = _family.rivals
