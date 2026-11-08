"""Thin native adapter loading only the adjacent count-relay prototype."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).resolve().with_name("prototype.py")
_BODY = _PATH.read_bytes()
_NAME = "_bf9e0959b8ce_count_relay_" + hashlib.sha256(
    str(_PATH).encode() + _BODY
).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent prototype: {_PATH}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _PROTOTYPE
exec(compile(_BODY, str(_PATH), "exec"), _PROTOTYPE.__dict__)

program = _PROTOTYPE.program
generate = _PROTOTYPE.generate
