from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.e5d9efdf472c import generator as gen
from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash, canonical_rule_source


TASK_ID = "e5d9efdf472c"
ROOT = Path(__file__).resolve().parents[1]
BASE_SOLUTION = ROOT / "data/base/solutions/banks/8edfaf6db623/E103__e5d9efdf472c.json"


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": gen.rule_mirror(grid)}


def test_rule_hash_and_selected_task_source_are_synchronized():
    assert gen.RULE_HASH == canonical_rule_hash(TASK_ID)
    row = json.loads(BASE_SOLUTION.read_text())
    assert row["racket_target"]["target_code"] == canonical_rule_source(TASK_ID)
    assert row["racket_target"]["raw_code"] != row["racket_target"]["target_code"]


def test_every_canonical_pair_is_owned_and_matches_the_semantic_mirror():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(copy.deepcopy(pair["input"])) == []
        assert gen.strict_canonical_like(copy.deepcopy(pair["input"])) == []
        assert gen.rule_mirror(copy.deepcopy(pair["input"])) == pair["output"]


def test_exact_override_boundaries_round_trip_and_unknown_axes_reject():
    cases = [
        {"grid_h": 7, "grid_w": 8, "orientation": "horizontal", "gap": 1, "decor_pattern": "single"},
        {"grid_h": 11, "grid_w": 12, "orientation": "vertical", "gap": 5, "decor_pattern": "adjacent_pair"},
        {"grid_h": 7, "grid_w": 8, "orientation": "vertical", "gap": 5, "decor_pattern": "separated_pair"},
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(8000 + index, index, difficulty="hard", **overrides)
        assert gen.observe_overrides(grid) == overrides
        assert gen.self_check(grid) == []
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, texture="horiz_axis")
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, __override_contract_unknown_axis__=1)


def test_default_curriculum_breaks_fixed_semantic_profile_correlations():
    keys = ("grid_h", "grid_w", "orientation", "gap", "decor_pattern")
    for band in ("easy", "medium", "hard"):
        observed = []
        for seed in range(24):
            for sample_index in range(8):
                axes = gen.observe_overrides(
                    gen.generate(seed, sample_index, difficulty=band)
                )
                observed.append(tuple(axes[key] for key in keys))

        signatures = set(observed)
        assert len(signatures) >= 24, (band, sorted(signatures))
        assert len({row[0] for row in signatures}) >= 2
        assert len({row[1] for row in signatures}) >= 3
        assert {row[2] for row in signatures} == set(gen.ORIENTATIONS)
        assert {row[3] for row in signatures} == set(range(1, 6))
        assert {row[4] for row in signatures} == set(gen.DECOR_PATTERNS)


def test_every_four_sample_window_is_identifiable_for_all_bands_and_start_residues():
    for band in ("easy", "medium", "hard"):
        for start in range(4):
            grids = [gen.generate(91000, start + offset, difficulty=band) for offset in range(5)]
            demos = [_pair(grid) for grid in grids[:4]]
            query = _pair(grids[4])
            assert gen.lesson_identifiable(demos, query) == []
            observed = [gen.observe_overrides(grid) for grid in grids[:4]]
            assert {row["orientation"] for row in observed} == {"horizontal", "vertical"}
            assert {row["decor_pattern"] for row in observed} == set(gen.DECOR_PATTERNS)
            assert min(row["gap"] for row in observed) <= 2
            assert max(row["gap"] for row in observed) >= 4


def test_separated_decoration_refutes_canonical_fitting_repeated_color_shortcut():
    assert all(
        gen._rival_connect_every_repeated_color(copy.deepcopy(pair["input"])) == pair["output"]
        for pair in canonical_pairs(TASK_ID)
    )
    grid = gen.generate(
        7001,
        2,
        difficulty="medium",
        decor_pattern="separated_pair",
    )
    assert gen.rule_mirror(grid) != gen._rival_connect_every_repeated_color(grid)


def test_longest_repeated_pair_rival_fits_canonical_but_fails_generated_witness():
    rival = getattr(gen, "_rival_connect_longest_repeated_pair", None)
    assert callable(rival)
    assert all(
        rival(copy.deepcopy(pair["input"])) == pair["output"]
        for pair in canonical_pairs(TASK_ID)
    )
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            grid = gen.generate(seed, 2, difficulty=band)
            assert gen.rule_mirror(grid) != rival(grid)


def test_short_separated_profile_makes_the_magenta_color_role_causal():
    for band in ("easy", "medium", "hard"):
        for seed in range(24):
            grid = gen.generate(seed, 2, difficulty=band)
            facts = gen.semantic_observables(grid)
            assert facts.get("decor_longer_than_marker") is True, (band, seed, facts)


def test_self_check_rejects_targeted_structural_impostors():
    base = gen.generate(12345, 0, difficulty="easy", decor_pattern="single")
    facts = gen._analyze(base)
    (r1, c1), (r2, c2) = facts["markers"]

    three_markers = copy.deepcopy(base)
    free = next(
        (r, c)
        for r, row in enumerate(three_markers)
        for c, value in enumerate(row)
        if value == 0 and (r, c) not in facts["interior"]
    )
    three_markers[free[0]][free[1]] = 6
    assert any("exactly two" in msg for msg in gen.self_check(three_markers))

    diagonal = copy.deepcopy(base)
    diagonal[r2][c2] = 0
    replacement = next(
        (r, c)
        for r in range(len(diagonal))
        for c in range(len(diagonal[0]))
        if diagonal[r][c] == 0 and r != r1 and c != c1
    )
    diagonal[replacement[0]][replacement[1]] = 6
    assert any("share exactly one row or column" in msg for msg in gen.self_check(diagonal))

    blocked = copy.deepcopy(base)
    ir, ic = facts["interior"][0]
    blocked[ir][ic] = 3
    assert any("interior must be zero" in msg for msg in gen.self_check(blocked))

    leaked_fill = copy.deepcopy(base)
    fill_cell = next(
        (r, c)
        for r, row in enumerate(leaked_fill)
        for c, value in enumerate(row)
        if value == 0 and (r, c) not in facts["interior"]
    )
    leaked_fill[fill_cell[0]][fill_cell[1]] = 8
    assert any("must not contain cyan" in msg for msg in gen.self_check(leaked_fill))


def test_replay_is_deterministic_fresh_and_does_not_touch_global_rng():
    random.seed(20260815)
    before = random.getstate()
    first = gen.generate(424242, 7, difficulty="hard")
    middle = random.getstate()
    second = gen.generate(424242, 7, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == middle == after
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second
