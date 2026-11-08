"""Native adapter loading only the exact adjacent task-local prototype."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_parametric_ebe910be6876_" + hashlib.sha256(
    str(_PATH).encode() + _PATH.read_bytes()
).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load ebe910be6876 parametric prototype")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _PROTOTYPE
_SPEC.loader.exec_module(_PROTOTYPE)

program = _PROTOTYPE.program
generate = _PROTOTYPE.generate
