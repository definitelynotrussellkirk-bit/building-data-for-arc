from __future__ import annotations

import copy
import importlib
import random

import pytest

from reviewer_support import canonical_pairs, find_root

GEN = importlib.import_module("puzzle_generators.per_puzzle.4dd0b3ed33ee.generator")
TASK_ID = "4dd0b3ed33ee"
ROOT = find_root(__file__)


def test_rule_hash_and_all_canonical_pairs_match_diagnostic_oracle():
    assert GEN.RULE_HASH == "a404f37f28fc"
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.oracle_output(pair["input"]) == pair["output"]


def test_canonical_ordered_tie_really_uses_first_match():
    pair = canonical_pairs(TASK_ID, root=ROOT)[0]
    _, _, matches = GEN._analysis(pair["input"])
    assert len(matches) == 2
    assert matches[0]["output"] == pair["output"]
    assert matches[1]["output"] != pair["output"]
    assert GEN.SEMANTIC_WITNESSES["two_matches_first_wins"](pair["input"])


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_determinism_oracle_and_global_rng_purity(difficulty):
    state = random.getstate()
    first = GEN.generate(seed=9173, sample_index=6, difficulty=difficulty)
    assert random.getstate() == state
    second = GEN.generate(seed=9173, sample_index=6, difficulty=difficulty)
    assert first == second
    assert GEN.self_check(first) == []
    assert GEN.oracle_output(first)


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 5, "grid_w": 15, "n_ones": 1},
        {"grid_h": 5, "grid_w": 15, "n_ones": 3},
        {"grid_h": 14, "grid_w": 22, "n_ones": 1},
        {"grid_h": 14, "grid_w": 22, "n_ones": 3},
    ],
)
def test_exact_boundary_overrides_are_observable(overrides):
    grid = GEN.generate(seed=3001, sample_index=3, **overrides)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == overrides


def test_unknown_and_out_of_domain_overrides_fail_loudly():
    with pytest.raises(ValueError, match="unknown override axis"):
        GEN.generate(seed=1, sample_index=0, texture="helpful")
    with pytest.raises(ValueError):
        GEN.generate(seed=1, sample_index=0, grid_h=4)
    with pytest.raises(ValueError, match="unknown difficulty"):
        GEN.generate(seed=1, sample_index=0, difficulty="nightmare")


def test_self_check_rejects_header_and_body_impostors():
    source = GEN.generate(seed=77, sample_index=2, grid_h=10, grid_w=18, n_ones=2)

    no_header = copy.deepcopy(source)
    no_header[0] = [0] * len(no_header[0])
    assert any("1..3 blue markers" in e for e in GEN.self_check(no_header))

    blue_in_body = copy.deepcopy(source)
    body_cell = next((r, c) for r in range(1, len(source)) for c, v in enumerate(source[r]) if v != 0)
    blue_in_body[body_cell[0]][body_cell[1]] = 1
    assert any("may not appear in the body" in e for e in GEN.self_check(blue_in_body))

    absent_match = copy.deepcopy(source)
    counts = {int(obj["holes"]) for obj in GEN._components(absent_match)}
    absent_k = next(k for k in (1, 2, 3) if k not in counts)
    absent_match[0] = [0] * len(absent_match[0])
    for c in range(absent_k):
        absent_match[0][c] = 1
    assert any("hole matches, got 0" in e for e in GEN.self_check(absent_match))


def test_self_check_rejects_same_answer_tie_and_touching_components():
    grid = [[0] * 15 for _ in range(5)]
    grid[0][0] = 1
    ring = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2))
    for dr, dc in ring:
        grid[1 + dr][1 + dc] = 2
        grid[1 + dr][4 + dc] = 3  # cardinally adjacent at the two bboxes
    errors = GEN.self_check(grid)
    assert any("may not touch" in e for e in errors)
    assert any("different answers" in e for e in errors)
