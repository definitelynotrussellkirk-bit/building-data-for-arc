"""Exact-path native adapter for the 94755460a402 command-source family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path


_PATH = Path(__file__).resolve().with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location(
    "_command_source_94755460a402_" + hashlib.sha256(str(_PATH).encode()).hexdigest(),
    _PATH,
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent prototype: {_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

program = _MODULE.program
generate = _MODULE.generate
analyze = _MODULE.analyze
solve = _MODULE.solve
teaching_check = _MODULE.teaching_check
public_challenge = _MODULE.public_challenge
public_turn = _MODULE.public_turn
controller_turns = _MODULE.controller_turns
counterfactual_program = _MODULE.counterfactual_program
