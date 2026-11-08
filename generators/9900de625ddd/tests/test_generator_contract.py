"""Regression tests for the window rule's input distribution and public controls.

The small Python erosion below is a test oracle only. Production labels remain
the unchanged canonical Racket program; workspace/review_probe.py checks that
authority separately over source-bound lessons.
"""
import importlib.util
import json
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location("selected_9900de625ddd", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def oracle(grid):
    out = [[0] * len(grid[0]) for _ in grid]
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            colors = {grid[y][x] for y in range(r - 1, r + 2)
                      for x in range(c - 1, c + 2)}
            if len(colors) == 1 and 0 not in colors:
                out[r][c] = grid[r][c]
    return out


def components(grid):
    unseen = {(r, c) for r, row in enumerate(grid)
              for c, value in enumerate(row) if value}
    result = []
    while unseen:
        todo = [unseen.pop()]
        part = set(todo)
        while todo:
            r, c = todo.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    part.add(point)
                    todo.append(point)
        result.append(part)
    return result


def rectangles_only_rival(grid):
    """Independent wrong rule: erode complete monochrome components only."""
    out = [[0] * len(grid[0]) for _ in grid]
    for part in components(grid):
        rs, cs = [r for r, c in part], [c for r, c in part]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        colors = {grid[r][c] for r, c in part}
        if len(colors) == 1 and len(part) == (r1 - r0 + 1) * (c1 - c0 + 1):
            for r in range(r0 + 1, r1):
                for c in range(c0 + 1, c1):
                    out[r][c] = grid[r][c]
    return out


def test_reported_rectangles_only_lesson_gap_is_repaired():
    # Candidate eb0c7abe let this rival survive all three demos; its hard
    # seed2 query3 contains a positive 3x3-with-tail that the rival drops.
    demos = [GEN.generate(2, index, difficulty="hard") for index in range(3)]
    assert any(rectangles_only_rival(grid) != oracle(grid) for grid in demos)


def test_corner_notch_is_a_positive_nonrectangular_overlap_case():
    grid = [[0] * 7 for _ in range(7)]
    for r in range(1, 5):
        for c in range(1, 5):
            grid[r][c] = 6
    grid[1][1] = 0
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid)["texture"] == "overlap"
    assert sum(value != 0 for row in oracle(grid) for value in row) == 3
    assert rectangles_only_rival(grid) != oracle(grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("case", [
    {"grid_h": 5, "grid_w": 24, "blocks": 6, "n_distinct_colors": 6, "texture": "3x3"},
    {"grid_h": 24, "grid_w": 5, "blocks": 6, "n_distinct_colors": 1, "texture": "3x3"},
    {"grid_h": 5, "grid_w": 5, "blocks": 1, "n_distinct_colors": 1, "texture": "overlap"},
    {"grid_h": 7, "grid_w": 7, "blocks": 3, "n_distinct_colors": 2, "texture": "contrast"},
    {"grid_h": 24, "grid_w": 24, "blocks": 6, "n_distinct_colors": 6, "texture": "contrast"},
])
def test_exact_controls_are_visible_even_at_geometry_boundaries(band, case):
    grid = GEN.generate(128, 7, difficulty=band, **case)
    assert GEN.self_check(grid) == []
    observed = GEN.observe_overrides(grid)
    assert all(observed[key] == value for key, value in case.items())
    assert len(grid) == case["grid_h"]
    assert len(grid[0]) == case["grid_w"]
    assert len(components(grid)) == case["blocks"]
    assert len({v for row in grid for v in row} - {0}) == case["n_distinct_colors"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("case", [
    {"grid_h": 5}, {"grid_w": 24}, {"blocks": 1}, {"blocks": 6},
    {"n_distinct_colors": 1}, {"n_distinct_colors": 6},
    {"texture": "3x3"}, {"texture": "overlap"}, {"texture": "contrast"},
])
def test_every_scalar_control_is_constructive_in_every_band(band, case):
    for seed in range(3):
        grid = GEN.generate(seed, seed, difficulty=band, **case)
        assert GEN.self_check(grid) == []
        obs = GEN.observe_overrides(grid)
        assert all(obs[key] == value for key, value in case.items())


@pytest.mark.parametrize("case", [
    {"grid_h": 5, "grid_w": 5, "blocks": 6},
    {"blocks": 1, "n_distinct_colors": 2},
    {"texture": "contrast", "blocks": 2},
    {"texture": "contrast", "n_distinct_colors": 1},
])
def test_impossible_combinations_fail_with_structured_axis_evidence(case):
    with pytest.raises(ValueError) as caught:
        GEN.generate(1, 0, **case)
    assert set(caught.value.incompatible_axes) <= set(case)
    assert len(caught.value.incompatible_axes) >= 2


@pytest.mark.parametrize("case", [
    {"unknown_axis": 4}, {"palette_kind": "warm"}, {"palette_size": 2},
    {"position_bias": "spaced_3x3_blocks"}, {"density": "sparse"},
    {"texture": "blocks_4x4"}, {"grid_h": True}, {"grid_w": 2},
    {"blocks": "2"}, {"n_distinct_colors": 7}, {"texture": None},
])
def test_bad_or_retired_controls_are_rejected(case):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(2, 0, **case)


@pytest.mark.parametrize("grid", [
    [], [[]], [[0], [0, 0]], [[True] * 7 for _ in range(7)],
    [[10] * 7 for _ in range(7)], [["0"] * 7 for _ in range(7)],
    [[0] * 7 for _ in range(7)], [[2] * 7 for _ in range(7)],
    [[2, 2], [2, 2]],
])
def test_validator_rejects_malformed_or_out_of_domain_grids_without_crashing(grid):
    assert GEN.self_check(grid)


def test_larger_blocks_have_all_overlapping_centers_and_no_degenerate_status():
    grid = [[0] * 7 for _ in range(7)]
    for r in range(1, 6):
        for c in range(1, 6):
            grid[r][c] = 3
    assert GEN.self_check(grid) == []
    assert sum(value != 0 for row in oracle(grid) for value in row) == 9
    assert GEN.RULE_HASH == "f64febd0911d"


def test_all_canonical_pairs_are_in_domain_and_fit_each_declared_shortcut():
    canonical = SOURCE.parents[2] / "shared/data/canonical/puzzles.jsonl"
    rows = (json.loads(line) for line in canonical.read_text().splitlines())
    task = next(row for row in rows if row["task_id"] == GEN.TASK_ID)
    pairs = task["train"] + task["test"]
    assert len(pairs) == 5
    assert GEN.CANONICAL_SHORTCUTS
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert oracle(pair["input"]) == pair["output"]
        for name, rival in GEN.CANONICAL_SHORTCUTS.items():
            assert rival(pair["input"]) == pair["output"], name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_cyclic_start_teaches_each_declared_rival(band):
    for seed in range(5):
        for start in range(GEN.SCHEDULE_PERIOD):
            grids = [GEN.generate(seed, start + offset, difficulty=band) for offset in range(4)]
            demos = [{"input": grid, "output": oracle(grid)} for grid in grids[:3]]
            query = {"input": grids[3], "output": oracle(grids[3])}
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(demo["input"]) != demo["output"] for demo in demos), name
            for grid in grids:
                assert GEN.strict_canonical_like(grid) == []
            assert grids == [GEN.generate(seed, start + offset, difficulty=band) for offset in range(4)]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_all_bands_retain_canonical_profiles_and_expanded_shapes(band):
    canonical_profiles = {(7, 12, 3), (8, 11, 4), (9, 9, 3), (9, 10, 3), (10, 10, 3)}
    grids = [GEN.generate(42, index, difficulty=band) for index in range(60)]
    hits = sum((len(g), len(g[0]), len({v for row in g for v in row}))
               in canonical_profiles for g in grids)
    assert hits >= 10
    assert {GEN.observe_overrides(g)["texture"] for g in grids} == {"3x3", "overlap", "contrast"}


def test_lesson_hook_names_surviving_rivals_in_a_canonical_only_lesson():
    grid = GEN.generate(3, 0, texture="3x3")
    demo = {"input": grid, "output": oracle(grid)}
    reasons = GEN.lesson_identifiable([demo, demo, demo], demo)
    assert reasons
    assert any("cross_centers" in reason for reason in reasons)
