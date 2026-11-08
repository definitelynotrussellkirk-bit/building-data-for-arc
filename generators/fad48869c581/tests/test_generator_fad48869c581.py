"""Focused safety tests for the isolated L-triomino generator."""
from __future__ import annotations

import copy
from pathlib import Path
import random
import sys

import pytest

_HERE = Path(__file__).resolve()
for _candidate in _HERE.parents:
    _runtime = _candidate / "shared" / "runtime"
    if (_runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(_runtime))
        break
from reviewer_support import canonical_pairs, find_root, load_selected_generator  # noqa: E402

TASK_ID = "fad48869c581"
ROOT = find_root(__file__)
gen, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def test_rule_mirror_matches_every_available_original_label():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) >= 3
    for pair in pairs:
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", [None, "medium"])
def test_ordinary_generation_is_deterministic_and_self_checked(difficulty):
    for seed in (0, 17, 2**63 - 1):
        for sample_index in range(8):
            first = gen.generate(seed, sample_index, difficulty=difficulty)
            second = gen.generate(seed, sample_index, difficulty=difficulty)
            assert first == second and first is not second
            assert gen.self_check(first, difficulty=difficulty) == []
            assert gen._fires(first)
            assert gen.rule_mirror(first) != first


def test_exact_axis_overrides_and_observer_include_30x30_stress():
    cases = [
        ({"grid_h": 7}, {"grid_h": 7}),
        ({"grid_w": 8}, {"grid_w": 8}),
        ({"n_blocks": 1}, {"n_blocks": 1}),
        ({"n_blocks": 10}, {"n_blocks": 10}),
        (
            {"grid_h": 30, "grid_w": 30, "n_blocks": 10},
            {"grid_h": 30, "grid_w": 30, "n_blocks": 10},
        ),
    ]
    for index, (overrides, expected) in enumerate(cases):
        grid = gen.generate(31, index, difficulty="medium", **overrides)
        observed = gen.observe_overrides(grid)
        for key, value in expected.items():
            assert observed[key] == value
        assert gen.self_check(grid, difficulty="medium", meta={"n_blocks": observed["n_blocks"]}) == []
    large = gen.generate(31, 99, difficulty="medium", grid_h=30, grid_w=30, n_blocks=10)
    assert sum(value != 0 for row in large for value in row) == 30
    for r0, c0 in ((0, 0), (0, 15), (15, 0), (15, 15)):
        assert sum(
            large[r][c] != 0
            for r in range(r0, r0 + 15)
            for c in range(c0, c0 + 15)
        ) >= 3


def test_unknown_and_incompatible_overrides_are_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, mystery=1)
    with pytest.raises(ValueError, match="cannot place"):
        gen.generate(0, 0, grid_h=3, grid_w=3, n_blocks=10)


def test_degenerate_modes_are_not_misreported_as_valid_lessons():
    for name in gen.DEGENERATE_TEXTURES:
        grid = gen.generate(0, 0, texture=name)
        assert gen.self_check(grid, difficulty="medium")


def test_global_random_state_and_return_aliases_are_clean():
    random.seed(881)
    before = random.getstate()
    first = gen.generate(12, 4, difficulty="medium")
    assert random.getstate() == before
    snapshot = copy.deepcopy(first)
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert gen.generate(12, 4, difficulty="medium") == snapshot
