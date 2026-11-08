"""Native adapter loading only this task's exact adjacent prototype."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_path = Path(__file__).with_name("prototype.py").resolve()
_name = "_row_corridor_" + hashlib.sha256(str(_path).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
if _spec is None or _spec.loader is None:  # pragma: no cover
    raise ImportError(_path)
_prototype = importlib.util.module_from_spec(_spec)
sys.modules[_name] = _prototype
_spec.loader.exec_module(_prototype)

program = _prototype.program
generate = _prototype.generate
