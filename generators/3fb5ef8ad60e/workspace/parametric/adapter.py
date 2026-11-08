"""Native adapter loading the exact adjacent divider-reference prototype."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).resolve().with_name("prototype.py")
_BODY = _PATH.read_bytes()
_NAME = "_3fb5ef8ad60e_parametric_" + hashlib.sha256(str(_PATH).encode() + _BODY).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent prototype: {_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _MODULE
exec(compile(_BODY, str(_PATH), "exec"), _MODULE.__dict__)

program = _MODULE.program
generate = _MODULE.generate
solve = _MODULE.solve
analyze = _MODULE.analyze
render_with_divider = _MODULE.render_with_divider
lesson_report = _MODULE.lesson_report
public_turn = _MODULE.public_turn
DIVIDER_REFERENCES = _MODULE.DIVIDER_REFERENCES
SETTINGS = _MODULE.SETTINGS
