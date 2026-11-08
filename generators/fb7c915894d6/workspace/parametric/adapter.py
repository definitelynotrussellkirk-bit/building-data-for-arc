"""Thin native adapter loading the exact adjacent repeated-shape prototype."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().with_name("prototype.py")
if _PATH.is_symlink() or not _PATH.is_file():
    raise ImportError("adapter requires its adjacent regular prototype.py")
_BODY = _PATH.read_bytes()
_NAME = "_fb7_parametric_" + hashlib.sha256(str(_PATH).encode() + _BODY).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
_MODULE = importlib.util.module_from_spec(_SPEC)
exec(compile(_BODY, str(_PATH), "exec"), _MODULE.__dict__)
program = _MODULE.program
generate = _MODULE.generate
