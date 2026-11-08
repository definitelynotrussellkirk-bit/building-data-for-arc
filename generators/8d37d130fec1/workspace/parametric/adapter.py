"""Native adapter loading only the exact adjacent candidate-choice prototype."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_path = Path(__file__).resolve().with_name("prototype.py")
_body = _path.read_bytes()
_name = "_candidate_choice_8d37d130fec1_" + hashlib.sha256(str(_path).encode() + _body).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
if _spec is None or _spec.loader is None:
    raise ImportError("cannot load adjacent 8d37d130fec1 prototype")
_module = importlib.util.module_from_spec(_spec)
sys.modules[_name] = _module
exec(compile(_body, str(_path), "exec"), _module.__dict__)

program = _module.program
generate = _module.generate
