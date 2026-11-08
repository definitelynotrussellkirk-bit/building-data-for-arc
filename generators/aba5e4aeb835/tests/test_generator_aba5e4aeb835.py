"""Regression cases for the canonical Mirror Laser Trace input contract."""
import importlib.util
import itertools
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
sys.path.insert(0, str(ROOT / "shared/runtime"))
SPEC = importlib.util.spec_from_file_location("laser_generator_under_test", HOME / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def canonical_pairs():
    for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == "aba5e4aeb835":
            return row["train"] + row["test"]
    raise AssertionError("canonical task missing")


@pytest.mark.parametrize("pair", canonical_pairs())
def test_accepts_each_canonical_input(pair):
    assert GEN.self_check(pair["input"]) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_inputs_have_real_border_source_and_mirrors(band):
    for index in range(16):
        grid = GEN.generate(17, index, difficulty=band)
        h, w = len(grid), len(grid[0])
        assert {v for row in grid for v in row} <= {0, 2, 3, 4, 5}
        starts = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
        assert len(starts) == 1
        r, c = starts[0]
        assert r in (0, h - 1) or c in (0, w - 1)
        assert sum(v in (3, 4) for row in grid for v in row) >= 2
        assert GEN.self_check(grid) == []


@pytest.mark.parametrize("grid", [[], [[]], [[0], [0, 2]], [[False]], [["2"]]])
def test_malformed_grids_return_violations_without_crashing(grid):
    assert GEN.self_check(grid)


def test_unknown_axis_is_rejected():
    with pytest.raises(ValueError):
        GEN.generate(0, 0, made_up_axis=3)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_explicit_grid_boundaries_work_in_every_band(band):
    grid = GEN.generate(0, 0, difficulty=band, grid_h=8, grid_w=8)
    assert (len(grid), len(grid[0])) == (8, 8)
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("pair", canonical_pairs())
def test_python_contract_trace_agrees_with_canonical_labels(pair):
    assert GEN._trace_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("side,mirror,exit_side", [
    ("top", 3, "left"), ("top", 4, "right"),
    ("right", 3, "bottom"), ("right", 4, "top"),
    ("bottom", 3, "right"), ("bottom", 4, "left"),
    ("left", 3, "top"), ("left", 4, "bottom"),
])
def test_all_eight_mirror_arrival_directions(side, mirror, exit_side):
    # Literal optical-direction table; expected cells do not use GEN helpers.
    source = {"top": (0, 3), "right": (3, 6), "bottom": (6, 3), "left": (3, 0)}[side]
    arms = {"top": {(0, 3), (1, 3), (2, 3)},
            "right": {(3, 4), (3, 5), (3, 6)},
            "bottom": {(4, 3), (5, 3), (6, 3)},
            "left": {(3, 0), (3, 1), (3, 2)}}
    grid = [[0] * 7 for _ in range(7)]
    grid[source[0]][source[1]] = 2
    grid[3][3] = mirror
    expected = [row[:] for row in grid]
    for r, c in (arms[side] - {source}) | arms[exit_side]:
        expected[r][c] = 8
    assert GEN._trace_output(grid) == expected


@pytest.mark.parametrize("profile,turns,side", list(itertools.product(
    range(4), range(2, 6), ("top", "right", "bottom", "left"))))
def test_exact_semantic_overrides_at_minimum_canvas(profile, turns, side):
    for walls, stop in ((0, 0), (1, 0), (1, 1), (4, 0), (4, 1)):
        requested = dict(grid_h=8, grid_w=8, path_turns=turns, source_side=side,
                         n_distractors=4, n_walls=walls, wall_stop=stop)
        grid = GEN.generate(17, profile, difficulty="hard", **requested)
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == requested
        assert sum(v in (3, 4) for row in grid for v in row) == turns + 4
        assert sum(v == 5 for row in grid for v in row) == walls


def test_declared_impossible_wall_request_fails():
    with pytest.raises(ValueError, match="incompatible"):
        GEN.generate(0, 0, n_walls=0, wall_stop=1)


@pytest.mark.parametrize("overrides", [
    {"grid_h": True}, {"path_turns": 2.1}, {"n_walls": "1"},
    {"source_side": 0}, {"source_side": "middle"}, {"grid_w": 21},
    {"path_turns": 6}, {"n_distractors": -1}, {"wall_stop": 2},
])
def test_invalid_override_values_are_not_coerced(overrides):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **overrides)


@pytest.mark.parametrize("band,start", list(itertools.product(("easy", "medium", "hard"), range(4))))
def test_all_cyclic_lesson_starts_refute_the_declared_rivals(band, start):
    pairs = []
    for index in range(start, start + 5):
        grid = GEN.generate(23, index, difficulty=band)
        pairs.append({"input": grid, "output": GEN._trace_output(grid)})
    assert GEN.lesson_identifiable(pairs[:4], {"input": pairs[4]["input"]}) == []


def test_canonical_only_lesson_exposes_actual_surviving_shortcuts():
    pairs = canonical_pairs()
    reasons = GEN.lesson_identifiable(pairs[:3], {"input": pairs[3]["input"]})
    assert any("max_three_reflections" in reason for reason in reasons)
    assert any("alternating_mirrors" in reason for reason in reasons)
    for rival in GEN.CANONICAL_SHORTCUTS.values():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs)


def test_cycle_uses_directional_state_and_terminates():
    grid = [[0] * 5 for _ in range(5)]
    for r, c, color in ((1, 1, 3), (1, 3, 4), (3, 3, 3), (3, 1, 4), (2, 1, 2)):
        grid[r][c] = color
    trace = GEN._trace(grid)
    assert trace["termination"] == "cycle"
    assert trace["painted"] == {(1, 2), (2, 3), (3, 2)}
    assert len(trace["walk"]) <= 4 * 5 * 5


def test_original_painted_color_stops_but_a_newly_painted_crossing_transmits():
    # Canonical example 1 crosses its initially painted source column.
    pair = canonical_pairs()[1]
    assert GEN._trace_output(pair["input"]) == pair["output"]
    grid = [[0] * 8 for _ in range(8)]
    grid[0][3] = 2
    grid[2][3] = 8
    expected = [row[:] for row in grid]
    expected[1][3] = 8
    assert GEN._trace_output(grid) == expected


def test_validation_rejects_domain_impostors():
    good = canonical_pairs()[0]["input"]
    for position, value in [((0, 0), 2), ((2, 2), 2), ((2, 2), 1), ((0, 5), 3)]:
        bad = [row[:] for row in good]
        bad[position[0]][position[1]] = value
        assert GEN.self_check(bad)
    interior = [row[:] for row in good]
    interior[4][0] = 0
    interior[4][1] = 2
    assert GEN.self_check(interior)


def test_generation_is_deterministic_and_contract_hooks_do_not_mutate_inputs():
    grid = GEN.generate(71, 3, difficulty="medium")
    snapshot = [row[:] for row in grid]
    GEN.self_check(grid)
    GEN.observe_overrides(grid)
    for fn in GEN.SEMANTIC_RIVALS.values():
        fn(grid)
    assert grid == snapshot
    assert GEN.generate(71, 3, difficulty="medium") == snapshot


def test_active_wall_hides_a_later_mirror_in_each_default_lesson():
    # Break caught: protecting the whole unobstructed route makes a conditional
    # "walls only stop after the last mirror" shortcut impossible to falsify.
    for seed in (0, 17, 104729):
        for band in ("easy", "medium", "hard"):
            grid = GEN.generate(seed, 1, difficulty=band)
            actual = GEN._trace(grid)
            through_wall = GEN._trace(grid, ignore_walls=True)
            assert len(through_wall["mirrors"]) > len(actual["mirrors"])
            assert GEN._trace_output(grid, ignore_walls=True) != GEN._trace_output(grid)
