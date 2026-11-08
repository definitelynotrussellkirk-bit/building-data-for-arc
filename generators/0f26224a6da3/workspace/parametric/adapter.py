"""Thin native adapter loading the exact adjacent isolated-source prototype."""
from __future__ import annotations

import hashlib
from pathlib import Path

_PATH = Path(__file__).resolve().with_name("prototype.py")
if _PATH.is_symlink() or not _PATH.is_file():
    raise ImportError("adapter requires its adjacent regular prototype.py")
_BODY = _PATH.read_bytes()
_NAME = "_0f26_parametric_" + hashlib.sha256(str(_PATH).encode() + _BODY).hexdigest()
_MODULE = type(__import__("sys"))(_NAME)
_MODULE.__file__ = str(_PATH)
exec(compile(_BODY, str(_PATH), "exec"), _MODULE.__dict__)
program = _MODULE.program
generate = _MODULE.generate
