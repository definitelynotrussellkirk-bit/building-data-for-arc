"""Exact-path adapter for three disjoint recoloring rules."""
import importlib.util
from pathlib import Path
_path = Path(__file__).resolve().with_name("union_family.py")
_spec = importlib.util.spec_from_file_location("recolor_union_adapter", _path)
_family = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_family)
program = _family.program
generate = _family.generate
analyze = _family.facts
transform = _family.transform
public_turn = _family.old.public_turn
rival_program = _family.old.rival_program
rival_transform = _family.rival_transform
RIVALS = _family.old.RIVALS
