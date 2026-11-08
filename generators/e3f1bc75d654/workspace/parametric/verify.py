#!/usr/bin/env python3
"""Compatibility entry point for the current bounded parametric audit."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys


_SOURCE = Path(__file__).resolve().with_name("audit.py")
_BODY = _SOURCE.read_bytes()
_NAME = "_e3f1bc75d654_audit_" + hashlib.sha256(
    str(_SOURCE).encode() + _BODY
).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _SOURCE)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent audit: {_SOURCE}")
_AUDIT = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _AUDIT
exec(compile(_BODY, str(_SOURCE), "exec"), _AUDIT.__dict__)

main = _AUDIT.main


if __name__ == "__main__":
    raise SystemExit(main())
