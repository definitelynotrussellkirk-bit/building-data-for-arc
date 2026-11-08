"""Thin native adapter loading only the exact adjacent prototype source."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_path = Path(__file__).resolve().with_name("prototype.py")
_name = "_stamp_transform_" + hashlib.sha256(str(_path).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
_prototype = importlib.util.module_from_spec(_spec)
sys.modules[_name] = _prototype
_spec.loader.exec_module(_prototype)
program = _prototype.program
generate = _prototype.generate
