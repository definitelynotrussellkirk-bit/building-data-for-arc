from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash

TASK_ID = "1279f507a3eb"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def test_rule_hash_and_canonical_inputs_are_owned() -> None:
    assert GEN.RULE_HASH == canonical_rule_hash(TASK_ID)
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 6
    assert all(GEN.self_check(copy.deepcopy(pair["input"])) == [] for pair in pairs)


def test_override_boundaries_are_exact_and_unknown_keys_reject() -> None:
    grid = GEN.generate(
        101,
        7,
        difficulty="easy",
        grid_h=12,
        grid_w=12,
        n_rings=2,
        n_distractors=3,
        edge_ring=False,
    )
    assert GEN.observe_overrides(grid) == {
        "grid_h": 12,
        "grid_w": 12,
        "n_rings": 2,
        "n_distractors": 3,
        "edge_ring": False,
    }
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(101, 7, typo_axis=1)


def test_single_ring_scene_kills_canonical_two_ring_shortcut() -> None:
    # Profile 1 deliberately contains one target ring, unlike every canonical
    # pair (which contains exactly two). The count-gated shortcut must disagree.
    grid = GEN.generate(202, 1, difficulty="easy")
    assert GEN.observe_overrides(grid)["n_rings"] == 1
    assert GEN._rival_two_ring_only(grid) != GEN._apply_rule(grid)


def test_every_two_demo_schedule_window_kills_count_and_edge_shortcuts() -> None:
    profiles = GEN._PROFILES
    for start in range(len(profiles)):
        window = [profiles[start], profiles[(start + 1) % len(profiles)]]
        assert any(profile["n_rings"] == 1 for profile in window)
        assert any(profile["edge_ring"] for profile in window)


def test_self_check_rejects_targeted_impostors() -> None:
    good = GEN.generate(303, 1, difficulty="medium")  # one-ring profile
    analysis = GEN._analyze(good)
    assert analysis["errors"] == []
    r0, c0 = analysis["ring_toplefts"][0]

    blank = [[0 for _ in row] for row in good]
    missing_perimeter = copy.deepcopy(good)
    missing_perimeter[r0][c0] = 0
    filled_center = copy.deepcopy(good)
    filled_center[r0 + 1][c0 + 1] = 1
    foreign_color = copy.deepcopy(good)
    foreign_color[0][0] = 2

    for impostor in (blank, missing_perimeter, filled_center, foreign_color):
        assert GEN.self_check(impostor)


def test_deterministic_fresh_returns_and_global_rng_preserved() -> None:
    random.seed(987654)
    state = random.getstate()
    first = GEN.generate(404, 5, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(404, 5, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert second[0][0] != 9
