"""Canonical rule and metadata regressions for generator 22398bb29643."""
from __future__ import annotations

import importlib

from reviewer_support import canonical_pairs, find_root


TASK_ID = "22398bb29643"
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.22398bb29643.generator"
)
ROOT = find_root(__file__)


def test_rule_pin_and_python_oracle_match_every_canonical_pair():
    assert GEN.GENERATOR_ID == TASK_ID
    assert GEN.TASK_ID == TASK_ID
    assert GEN.RULE_HASH == "bea915e9e998"

    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
