"""Focused regression tests for selector-guided motif broadcast."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


TASK_ID = "81cced17d473"
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.81cced17d473.generator"
)


def _pair(grid):
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs_are_pinned():
    assert GEN.RULE_HASH == canonical_rule_hash(TASK_ID) == "8f04dcabcbe7"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]

    # The second canonical input deliberately has a decoy whose projection at
    # the right-edge anchors is out of bounds.  Decoys are ignored, so the
    # structural checker must not reject this authority-valid boundary case.
    facts, errors = GEN._analyze(pairs[1]["input"])
    assert errors == []
    assert any(
        not (0 <= ar + dr < facts["grid_h"] and 0 <= ac + dc < facts["grid_w"])
        for ar, ac in facts["anchors"]
        for dr, dc, _ in facts["decoy_offsets"]
    )


def test_all_exact_axes_round_trip_at_boundaries_in_every_band():
    cases = (
        {
            "grid_h": 9,
            "grid_w": 9,
            "target_color": 1,
            "n_anchors": 2,
            "texture": "single_decoy",
        },
        {
            "grid_h": 14,
            "grid_w": 14,
            "target_color": 9,
            "n_anchors": 3,
            "texture": "expanded_far",
        },
    )
    for band in ("easy", "medium", "hard"):
        for index, overrides in enumerate(cases):
            grid = GEN.generate(800 + index, index, difficulty=band, **overrides)
            assert GEN.observe_overrides(grid) == overrides
            assert GEN.self_check(grid, meta={"overrides": overrides}) == []
            assert GEN.rule_mirror(grid) != grid


def test_each_profile_is_constructible_and_kills_its_declared_rivals():
    for band in ("easy", "medium", "hard"):
        for index, profile in enumerate(GEN.SCHEDULE_PROFILES):
            grid = GEN.generate(
                1700 + index,
                index,
                difficulty=band,
                texture=profile,
            )
            observed = GEN.observe_overrides(grid)
            assert observed["texture"] == profile
            official = GEN.rule_mirror(grid)
            for rival_name in GEN.WITNESS_RIVALS[profile]:
                assert official != GEN.SEMANTIC_RIVALS[rival_name](grid)


def test_canonical_shortcuts_fit_public_pairs_but_generated_witnesses_kill_them():
    pairs = canonical_pairs(TASK_ID)
    for rival in GEN.CANONICAL_SHORTCUTS.values():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs)

    modal = GEN.generate(9, 2, texture="modal_decoy")
    expanded = GEN.generate(9, 3, texture="expanded_far")
    assert GEN.CANONICAL_SHORTCUTS["modal_local_color"](modal) != GEN.rule_mirror(modal)
    assert GEN.CANONICAL_SHORTCUTS["first_two_selected"](expanded) != GEN.rule_mirror(expanded)


def test_every_sliding_four_demo_window_is_identifiable():
    checked = 0
    for band in ("easy", "medium", "hard"):
        for seed in range(6):
            rows = [_pair(GEN.generate(seed, index, difficulty=band)) for index in range(20)]
            for start in range(16):
                demos = rows[start : start + GEN.EXAMPLES_NEEDED]
                query = rows[start + GEN.EXAMPLES_NEEDED]
                assert GEN.lesson_identifiable(demos, query) == []
                checked += 1
    assert checked == 288


def test_self_check_rejects_four_targeted_impostors():
    grid = GEN.generate(42, 3, difficulty="medium", texture="expanded_far")
    facts, errors = GEN._analyze(grid)
    assert errors == []

    no_source = copy.deepcopy(grid)
    sr, sc = facts["source"]
    no_source[sr][sc] = 0
    assert any("exactly one gray" in reason for reason in GEN.self_check(no_source))

    no_decoys = copy.deepcopy(grid)
    for row, col, _ in facts["decoy_cells"]:
        no_decoys[row][col] = 0
    assert any("local decoy" in reason for reason in GEN.self_check(no_decoys))

    # Negative recombination: replace the selector with a color absent from the
    # entire remaining scene.  The Racket oracle can execute this identity
    # case, but it is a rule-hiding lesson and the teaching grammar rejects it.
    absent_selector = copy.deepcopy(grid)
    used = {value for row in grid for value in row}
    replacement = next(color for color in (1, 2, 3, 4, 7, 8, 9) if color not in used)
    absent_selector[0][0] = replacement
    assert any("selected-color motif" in reason for reason in GEN.self_check(absent_selector))
    assert GEN.rule_mirror(absent_selector) == absent_selector

    occupied_landing = copy.deepcopy(grid)
    ar, ac = facts["anchors"][0]
    dr, dc = facts["motif_offsets"][0]
    occupied_landing[ar + dr][ac + dc] = facts["decoy_cells"][0][2]
    assert any("selected landing" in reason for reason in GEN.self_check(occupied_landing))


def test_generated_decoy_projections_are_clean_copy_all_witnesses():
    for band in ("easy", "medium", "hard"):
        for sample_index in range(24):
            grid = GEN.generate(2026, sample_index, difficulty=band)
            facts, errors = GEN._analyze(grid)
            assert errors == []
            for ar, ac in facts["anchors"]:
                for dr, dc, _ in facts["decoy_offsets"]:
                    rr, cc = ar + dr, ac + dc
                    assert 0 <= rr < facts["grid_h"]
                    assert 0 <= cc < facts["grid_w"]
                    assert grid[rr][cc] == 0


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(123456)
    before = random.getstate()
    first = GEN.generate(91, 23, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(91, 23, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert GEN.generate(91, 23, difficulty="hard") == second


def test_unknown_override_and_difficulty_fail_closed():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, typo_axis=1)
    with pytest.raises(ValueError, match="difficulty must be"):
        GEN.generate(0, 0, difficulty="extreme")
