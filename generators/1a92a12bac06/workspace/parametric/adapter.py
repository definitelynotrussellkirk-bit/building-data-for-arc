"""Native entry point; load the adjacent family by its exact path."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_path = Path(__file__).resolve().with_name("family.py")
_name = "_half_relay_family_" + hashlib.sha256(str(_path).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
family = importlib.util.module_from_spec(_spec)
sys.modules[_name] = family
_spec.loader.exec_module(family)

program = family.program
generate = family.generate
sample_input = family.sample_input
transform = family.transform
half_fill = family.half_fill
relay_state = family.relay_state
wrong_order_transform = family.wrong_order_transform
counterfactual_program = family.counterfactual_program
public_turn = family.public_turn
