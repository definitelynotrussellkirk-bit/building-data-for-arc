"""Thin native adapter for the 85d01dd02c6d wall-scope family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path


_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_arc_85d01dd02c6d_wall_scope_" + hashlib.sha256(str(_PATH).encode()).hexdigest()[:16]
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load parametric prototype at {_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

program = _MODULE.program
generate = _MODULE.generate
solve_python = _MODULE.solve_python
analyze_scene = _MODULE.analyze_scene
public_challenge = _MODULE.public_challenge
public_turn = _MODULE.public_turn
controller_turns = _MODULE.controller_turns
