"""Native adapter bound to the adjacent marker-assignment prototype."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_name = "_b650_marker_assignment_" + hashlib.sha256(str(_path).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
if _spec is None or _spec.loader is None:  # pragma: no cover - import machinery guard
    raise ImportError(f"cannot load adjacent prototype: {_path}")
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)

program = _prototype.program
generate = _prototype.generate
