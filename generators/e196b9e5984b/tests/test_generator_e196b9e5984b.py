from __future__ import annotations

import copy
import importlib
import random
import pytest

from scripts.canonical_profile_gate import canonical_pairs

GEN = importlib.import_module("puzzle_generators.per_puzzle.e196b9e5984b.generator")
TASK_ID = "e196b9e5984b"


def _shortest_count(grid):
    portals = GEN._portals(grid)
    walkable = GEN._walkable(grid)
    return GEN._shortest_path_stats(walkable, portals[0][:2], portals[1][:2])


def _episode(seed, start, difficulty):
    pairs = []
    for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
        grid = GEN.generate(seed=seed, sample_index=sample_index, difficulty=difficulty)
        pairs.append({"input": grid, "output": GEN.oracle_output(grid)})
    return pairs[:-1], pairs[-1]


def test_rule_hash_canonical_pairs_and_authoritative_order():
    assert GEN.RULE_HASH == "d55a733c2b68"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    counts = []
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.oracle_output(pair["input"]) == pair["output"]
        assert pair["input"] == before
        counts.append(_shortest_count(pair["input"])[1])
    assert counts == [2, 4, 1]


def test_canonical_pairs_leave_two_priority_shortcuts_alive():
    pairs = canonical_pairs(TASK_ID)
    for order in ("RLDU", "RDUL"):
        assert all(GEN._output_for_order(pair["input"], order) == pair["output"] for pair in pairs)
    assert any(GEN._output_for_order(pair["input"], "DRLU") != pair["output"] for pair in pairs)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_four_sample_window_identifies_the_rule(difficulty):
    for start in range(8):
        demos, query = _episode(seed=19391 + start, start=start, difficulty=difficulty)
        assert {GEN.schedule_profile(0, start + i) for i in range(4)} == set(GEN.SCHEDULE_PROFILES)
        assert GEN.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize(
    ("sample_index", "profile", "rival"),
    [
        (0, "unique_detour", "row_then_column"),
        (1, "right_before_down_tie", "down_before_right"),
        (2, "down_before_left_tie", "left_before_down"),
        (3, "left_before_up_tie", "up_before_left"),
    ],
)
def test_scheduled_profiles_realize_and_kill_their_rival(sample_index, profile, rival):
    grid = GEN.generate(seed=7713, sample_index=sample_index, difficulty="hard")
    assert GEN.schedule_profile(7713, sample_index, "hard") == profile
    assert GEN.strict_canonical_like(grid) == []
    witness = "unique_shortest_detour" if profile == "unique_detour" else profile
    assert GEN.SEMANTIC_WITNESSES[witness](grid)
    assert GEN.SEMANTIC_RIVALS[rival](grid) != GEN.oracle_output(grid)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_determinism_fresh_objects_oracle_and_global_rng_purity(difficulty):
    state = random.getstate()
    first = GEN.generate(seed=9173, sample_index=6, difficulty=difficulty)
    assert random.getstate() == state
    second = GEN.generate(seed=9173, sample_index=6, difficulty=difficulty)
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert GEN.strict_canonical_like(first) == []
    assert GEN.oracle_output(first) != first


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 7, "grid_w": 9, "portal_color": 1},
        {"grid_h": 7, "grid_w": 13, "portal_color": 9},
        {"grid_h": 11, "grid_w": 9, "portal_color": 2},
        {"grid_h": 11, "grid_w": 13, "portal_color": 8},
    ],
)
def test_exact_boundary_overrides_are_observable(overrides):
    grid = GEN.generate(seed=3001, sample_index=3, difficulty="hard", **overrides)
    assert GEN.strict_canonical_like(grid) == []
    assert GEN.observe_overrides(grid) == overrides


def test_unknown_out_of_domain_overrides_and_difficulty_fail_loudly():
    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(seed=1, sample_index=0, texture="helpful")
    for name, value in (("grid_h", 8), ("grid_w", 10), ("portal_color", 5)):
        with pytest.raises(ValueError):
            GEN.generate(seed=1, sample_index=0, **{name: value})
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(seed=1, sample_index=0, difficulty="nightmare")


def test_self_check_rejects_targeted_impostors_and_recombination():
    source = GEN.generate(seed=77, sample_index=2, grid_h=11, grid_w=13, portal_color=2)
    portals = GEN._portals(source)
    zeros = [(r, c) for r, row in enumerate(source) for c, v in enumerate(row) if v == 0]

    no_portal = copy.deepcopy(source)
    no_portal[portals[0][0]][portals[0][1]] = 0
    assert GEN.self_check(no_portal)

    mismatched = copy.deepcopy(source)
    mismatched[portals[1][0]][portals[1][1]] = 7
    assert any("same color" in error for error in GEN.self_check(mismatched))

    third_portal = copy.deepcopy(source)
    third_portal[zeros[0][0]][zeros[0][1]] = portals[0][2]
    assert any("exactly two" in error for error in GEN.self_check(third_portal))

    broken_border = copy.deepcopy(source)
    broken_border[0][1] = 0
    assert any("outer border" in error for error in GEN.self_check(broken_border))

    disconnected = copy.deepcopy(source)
    pr, pc, _ = portals[0]
    for dr, dc in GEN._DIRECTIONS.values():
        rr, cc = pr + dr, pc + dc
        if disconnected[rr][cc] == 0:
            disconnected[rr][cc] = 5
    assert any("one component" in error or "connected" in error for error in GEN.self_check(disconnected))

    invalid_color = copy.deepcopy(source)
    invalid_color[zeros[0][0]][zeros[0][1]] = 10
    assert any("0..9" in error for error in GEN.self_check(invalid_color))

    ragged = copy.deepcopy(source)
    ragged[1].pop()
    assert any("rectangular" in error for error in GEN.self_check(ragged))

    donor = GEN.generate(seed=78, sample_index=2, grid_h=11, grid_w=13, portal_color=7)
    recombined = copy.deepcopy(source)
    dr, dc, donor_color = GEN._portals(donor)[1]
    # Recombine a portal attribute from another lawful scene without importing its mate.
    sr, sc, _ = GEN._portals(recombined)[1]
    recombined[sr][sc] = donor_color
    assert any("same color" in error for error in GEN.self_check(recombined))
