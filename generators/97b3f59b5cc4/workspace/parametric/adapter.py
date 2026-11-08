"""Native promotion adapter for the connectivity family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_SOURCE = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_arc_97b3f59b5cc4_connectivity_" + hashlib.sha256(str(_SOURCE).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _SOURCE)
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover - import guard
    raise ImportError(f"cannot load sibling prototype: {_SOURCE}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _PROTOTYPE
exec(compile(_SOURCE.read_bytes(), str(_SOURCE), "exec"), _PROTOTYPE.__dict__)

program = _PROTOTYPE.program
generate = _PROTOTYPE.generate
