"""Thin native adapter bound to the exact adjacent overlap-size relay prototype."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_SOURCE = Path(__file__).resolve().with_name("prototype.py")
_BODY = _SOURCE.read_bytes()
_NAME = "_arc_139d29b1283d_parametric_" + hashlib.sha256(str(_SOURCE).encode() + _BODY).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _SOURCE)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent parametric prototype")
_FAMILY = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _FAMILY
exec(compile(_BODY, str(_SOURCE), "exec"), _FAMILY.__dict__)

program = _FAMILY.program
generate = _FAMILY.generate
