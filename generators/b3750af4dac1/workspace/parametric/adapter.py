"""Native entry point loaded from this target's adjacent family source."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_path = Path(__file__).resolve().with_name("family.py")
_name = "_b3750af4dac1_parametric_" + hashlib.sha256(str(_path).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"cannot load family from {_path}")
_family = importlib.util.module_from_spec(_spec)
sys.modules[_name] = _family
_spec.loader.exec_module(_family)

program = _family.program
generate = _family.generate
sample_input = _family.sample_input
transform = _family.transform
match_state = _family.match_state
wrong_intermediate_transform = _family.wrong_intermediate_transform
counterfactual_program = _family.counterfactual_program
strip_neighbor_program = _family.strip_neighbor_program
query_neighbor_program = _family.query_neighbor_program
all_candidate_program = _family.all_candidate_program
area_only_program = _family.area_only_program
degree_only_program = _family.degree_only_program
first_candidate_program = _family.first_candidate_program
public_turn = _family.public_turn
