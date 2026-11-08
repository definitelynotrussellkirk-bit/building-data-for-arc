"""Generate divider-scrambled boundary-port chains for public parent 78332cb0."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

GENERATOR_ID = TASK_ID = "public_eval_78332cb0"
RULE_TASK_ID = "ee_78332cb0"
VERSION = "1.0.0"
EXAMPLES_NEEDED = 2
SUMMARY = "Reorder unchanged separator-delimited panels into their boundary-port chain."
AXES = {}
INVARIANTS = [
    "one repeated non-background divider color partitions equal panels",
    "panel ports define one all-panel chain on exactly one opposite-edge axis",
    "ordinary generator returns inputs only; reference.rkt owns labels",
]

_path = Path(__file__).resolve().parent / "workspace/parametric/family.py"
_spec = importlib.util.spec_from_file_location("_chain_78332cb0_generator_family", _path)
_family = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _family
_spec.loader.exec_module(_family)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if overrides:
        raise TypeError("No generation overrides are declared")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("Unknown difficulty")
    offset = 9 if difficulty == "hard" else sample_index % 10
    return _family.sample(seed + 1000003 * (sample_index // 10), "train", offset)


def self_check(grid, *, difficulty=None, meta=None):
    try:
        _family.analyze(grid)
    except (TypeError, ValueError, IndexError) as error:
        return [str(error)]
    return []
