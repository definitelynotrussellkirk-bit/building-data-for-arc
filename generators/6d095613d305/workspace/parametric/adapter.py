"""Thin native adapter loading only the adjacent polyline family source."""
from __future__ import annotations
import hashlib
import importlib.util
from pathlib import Path
import sys
_path = Path(__file__).resolve().with_name("family.py")
_name = "_parametric_6d095613d305_" + hashlib.sha256(str(_path).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
if _spec is None or _spec.loader is None:
    raise ImportError(_path)
_family = importlib.util.module_from_spec(_spec)
sys.modules[_name] = _family
_spec.loader.exec_module(_family)
program = _family.program
generate = _family.generate
public_turn = _family.public_turn
