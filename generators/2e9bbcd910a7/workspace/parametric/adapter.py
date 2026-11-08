"""Thin native adapter for the causal diagonal-follower prototype."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path


_path = Path(__file__).resolve().with_name("prototype.py")
_name = "_arc_2e9bbcd910a7_parametric_" + hashlib.sha256(str(_path).encode()).hexdigest()[:16]
_spec = importlib.util.spec_from_file_location(_name, _path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"cannot load parametric prototype at {_path}")
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)

program = _prototype.program
generate = _prototype.generate
solve_python = _prototype.solve_python
select_crossing_follower = _prototype.select_crossing_follower

public_challenge = _prototype.public_challenge
public_turn = _prototype.public_turn
controller_turns = _prototype.controller_turns
