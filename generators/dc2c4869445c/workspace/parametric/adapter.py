"""Native adapter loading the adjacent reflection-selection prototype exactly."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_dc2c4869445c_reflection_selection", _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

program = _module.program
generate = _module.generate
transform = _module.transform
candidates = _module.candidates
winner = _module.winner
teaching_report = _module.teaching_report
public_turn = _module.public_turn
rival_names = _module.rival_names
rival_output = _module.rival_output
rival_program = _module.rival_program
causal_state = _module.causal_state
validate_grid = _module.validate_grid
