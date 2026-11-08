"""Focused regressions for request validation and canonical-shortcut metadata."""
from __future__ import annotations

import copy
import importlib

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "474634a9f7b7"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


@pytest.mark.parametrize(
    ("seed", "sample_index", "kwargs"),
    [
        (True, 0, {}),
        (1.0, 0, {}),
        ("1", 0, {}),
        (0, True, {}),
        (0, 1.0, {}),
        (0, "1", {}),
        (0, -1, {}),
        (0, 0, {"difficulty": True}),
        (0, 0, {"difficulty": 0}),
        (0, 0, {"difficulty": 1.0}),
        (0, 0, {"difficulty": "expert"}),
        (0, 0, {"grid_h": 16.0}),
        (0, 0, {"grid_w": True}),
        (0, 0, {"target_size": "16"}),
        (0, 0, {"target_side": 1}),
        (0, 0, {"shape_family": True}),
    ],
)
def test_public_request_contract_rejects_scalar_coercion(seed, sample_index, kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(seed, sample_index, **kwargs)


def test_canonical_shortcuts_name_only_rules_that_fit_every_canonical_pair():
    assert set(MODULE.CANONICAL_SHORTCUTS) == {"top_or_right_only"}
    shortcut = MODULE.CANONICAL_SHORTCUTS["top_or_right_only"]
    for pair in _canonical_pairs():
        assert shortcut(copy.deepcopy(pair["input"])) == pair["output"]

    for target_side in ("bottom", "left"):
        grid = MODULE.generate(
            20261019,
            2 if target_side == "bottom" else 3,
            difficulty="hard",
            target_side=target_side,
        )
        assert MODULE.self_check(grid) == []
        assert shortcut(copy.deepcopy(grid)) != MODULE.rule_mirror(grid)
