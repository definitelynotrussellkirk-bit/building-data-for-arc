"""Thin native adapter for the causal farthest-relay BFS family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path


_path = Path(__file__).resolve().with_name("prototype.py")
_name = "_arc_9199b47fab1e_parametric_" + hashlib.sha256(str(_path).encode()).hexdigest()[:16]
_spec = importlib.util.spec_from_file_location(_name, _path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"cannot load parametric prototype at {_path}")
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)

program = _prototype.program
generate = _prototype.generate
solve_python = _prototype.solve_python
solve_from_relay = _prototype.solve_from_relay
analyze = _prototype.analyze
teaching_check = _prototype.teaching_check
public_turn = _prototype.public_turn
