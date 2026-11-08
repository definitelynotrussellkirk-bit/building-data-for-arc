"""Portable regressions for the rectangle-completion generator contract.

The geometry helpers here are deliberately independent of production rivals.
Only the canonical Racket authority labels exported lessons; this test oracle is
used to verify source-domain geometry and the retained counterexample.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK = "1acd7639146e"
ROOT = find_root(__file__)
TASK_HOME = next(
    p for p in Path(__file__).resolve().parents
    if (p / "generator.py").is_file()
)
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", TASK_HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location("rectangle_generator_under_test", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GEN)


def positions(grid):
    result = {}
    for color in (1, 2, 3):
        hits = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        assert len(hits) == 1
        result[color] = hits[0]
    return result


def observed(grid):
    p = positions(grid)
    r1, c1 = p[1]
    r2, c2 = p[2]
    r3, c3 = p[3]
    orientation = {
        (1, 1): 0,   # shared corner top-left
        (1, -1): 1,  # top-right
        (-1, 1): 2,  # bottom-left
        (-1, -1): 3, # bottom-right
    }[((r3 > r1) - (r3 < r1), (c2 > c1) - (c2 < c1))]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "rect_h": abs(r3 - r1) + 1,
        "rect_w": abs(c2 - c1) + 1,
        "orientation": orientation,
    }


def expected_outline(grid):
    p = positions(grid)
    top, bottom = sorted((p[1][0], p[3][0]))
    left, right = sorted((p[1][1], p[2][1]))
    out = [[0 for _ in row] for row in grid]
    for c in range(left, right + 1):
        out[top][c] = 8
        out[bottom][c] = 8
    for r in range(top, bottom + 1):
        out[r][left] = 8
        out[r][right] = 8
    return out


def witness_flags(grid):
    stats = observed(grid)
    p = positions(grid)
    top, bottom = sorted((p[1][0], p[3][0]))
    left, right = sorted((p[1][1], p[2][1]))
    return {
        "unseen_orientation": stats["orientation"] == 2,
        "border_contact": top == 0 or left == 0 or bottom == len(grid) - 1 or right == len(grid[0]) - 1,
        "compact": stats["rect_h"] < 5 or stats["rect_w"] < 6,
        "extreme_aspect": abs(stats["rect_h"] - stats["rect_w"]) > 1,
    }


def pair(grid):
    return {"input": grid, "output": expected_outline(grid)}


def test_rule_pin_and_curriculum_contract_are_explicit():
    assert GEN.RULE_HASH == "695d22e3417f"
    assert GEN.VERSION == "3.0.0"
    assert GEN.EXAMPLES_NEEDED == 4
    assert GEN.LESSON_SCHEDULE_PERIOD == 4
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("orientation", range(4))
@pytest.mark.parametrize("rect_h,rect_w", [(3, 3), (3, 6), (6, 3), (6, 6)])
def test_every_joint_exact_control_is_realized_in_every_band(band, orientation, rect_h, rect_w):
    options = {
        "grid_h": 6,
        "grid_w": 6,
        "rect_h": rect_h,
        "rect_w": rect_w,
        "orientation": orientation,
    }
    grid = GEN.generate(17, orientation + rect_h * 10 + rect_w, difficulty=band, **options)
    assert GEN.self_check(grid) == []
    assert observed(grid) == options
    assert GEN.observe_overrides(grid) == options
    assert grid == GEN.generate(17, orientation + rect_h * 10 + rect_w, difficulty=band, **options)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("height,width", [(6, 6), (18, 18), (6, 18), (18, 6)])
def test_canvas_boundaries_are_exact_and_constructive(band, height, width):
    grid = GEN.generate(91, height + width, difficulty=band,
                        grid_h=height, grid_w=width, rect_h=6, rect_w=6, orientation=3)
    assert observed(grid) == {
        "grid_h": height, "grid_w": width, "rect_h": 6, "rect_w": 6, "orientation": 3,
    }
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("overrides", [
    {"typo": 1}, {"texture": "missing_color_1"}, {"palette_kind": "warm"},
    {"grid_h": True}, {"grid_h": 6.0}, {"grid_w": "6"},
    {"rect_h": False}, {"rect_w": 3.0}, {"orientation": "1"},
    {"grid_h": 5}, {"grid_h": 19}, {"grid_w": 5}, {"grid_w": 19},
    {"rect_h": 2}, {"rect_h": 7}, {"rect_w": 2}, {"rect_w": 7},
    {"orientation": -1}, {"orientation": 4},
])
def test_invalid_or_retired_controls_fail_explicitly(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **overrides)


def test_none_means_no_override_and_invalid_difficulty_fails():
    expected = GEN.generate(5, 7, difficulty="medium")
    assert GEN.generate(5, 7, difficulty="medium", grid_h=None, grid_w=None,
                        rect_h=None, rect_w=None, orientation=None) == expected
    with pytest.raises(ValueError):
        GEN.generate(5, 7, difficulty="expert")


@pytest.mark.parametrize("bad", [
    None, [], [[]], [[0], [0, 0]], [[True] * 6 for _ in range(6)],
    [[1.5] + [0] * 5 for _ in range(6)], [[10] + [0] * 5 for _ in range(6)],
    [[0] * 6 for _ in range(5)], [[0] * 19 for _ in range(6)],
])
def test_validator_rejects_malformed_grids_without_throwing(bad):
    assert GEN.self_check(bad)


@pytest.mark.parametrize("mutation", [
    "missing_1", "duplicate_2", "wrong_row", "wrong_col", "too_short_h", "too_short_w", "unknown_color",
])
def test_validator_rejects_out_of_domain_marker_geometry(mutation):
    grid = GEN.generate(44, 3, grid_h=8, grid_w=8, rect_h=4, rect_w=4, orientation=0)
    p = positions(grid)
    if mutation == "missing_1":
        r, c = p[1]; grid[r][c] = 0
    elif mutation == "duplicate_2":
        grid[7][7] = 2
    elif mutation == "wrong_row":
        r, c = p[2]; grid[r][c] = 0; grid[r + 1][c] = 2
    elif mutation == "wrong_col":
        r, c = p[3]; grid[r][c] = 0; grid[r][c + 1] = 3
    elif mutation == "too_short_h":
        r1, c1 = p[1]; r3, c3 = p[3]; grid[r3][c3] = 0; grid[r1 + 1][c1] = 3
    elif mutation == "too_short_w":
        r1, c1 = p[1]; r2, c2 = p[2]; grid[r2][c2] = 0; grid[r1][c1 + 1] = 2
    else:
        grid[7][7] = 4
    assert GEN.self_check(grid)


def test_all_canonical_pairs_stay_supported_and_match_independent_geometry():
    rows = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert len(rows) == 3
    for row in rows:
        assert GEN.self_check(row["input"]) == []
        assert GEN.strict_canonical_like(row["input"]) == []
        assert expected_outline(row["input"]) == row["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_covers_all_orientations_sizes_and_edges(band):
    orientations, shapes, rects = set(), set(), set()
    flags = {name: 0 for name in ("unseen_orientation", "border_contact", "compact", "extreme_aspect")}
    for index in range(96):
        grid = GEN.generate(700 + index, index, difficulty=band)
        assert GEN.self_check(grid) == []
        stats = observed(grid)
        orientations.add(stats["orientation"])
        shapes.add((stats["grid_h"], stats["grid_w"]))
        rects.add((stats["rect_h"], stats["rect_w"]))
        for name, value in witness_flags(grid).items():
            flags[name] += int(value)
    assert orientations == {0, 1, 2, 3}
    assert len(shapes) >= 8
    assert len(rects) >= 6
    assert all(count >= 40 for count in flags.values()), flags


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_cyclic_window_survives_every_query_holdout(band):
    # EXAMPLES_NEEDED=4 means each materialized lesson has five labelled pairs.
    # Rich profiles jointly refute every declared canonical shortcut; requiring
    # at least two rich demonstrations makes any single held-out pair safe.
    for seed in (0, 1, 17, 99):
        grids = [GEN.generate(seed, index, difficulty=band) for index in range(16)]
        for start in range(12):
            window = grids[start:start + 5]
            for held in range(5):
                demos = [grid for i, grid in enumerate(window) if i != held]
                for feature in ("unseen_orientation", "border_contact", "compact", "extreme_aspect"):
                    assert sum(witness_flags(grid)[feature] for grid in demos) >= 2, (
                        band, seed, start, held, feature,
                        [witness_flags(grid) for grid in window],
                    )
                assert GEN.lesson_identifiable([pair(grid) for grid in demos], pair(window[held])) == []


def test_declared_shortcuts_fit_every_canonical_pair_but_fail_joint_witness():
    canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    witness = GEN.generate(123, 1, difficulty="medium")
    flags = witness_flags(witness)
    assert all(flags.values()), flags
    assert len(GEN.CANONICAL_SHORTCUTS) >= 4
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(row["input"]) == row["output"] for row in canonical), name
        assert rival(witness) != expected_outline(witness), name


def test_lesson_hook_reports_real_ambiguity_and_accepts_refuting_examples():
    canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    witness = GEN.generate(123, 1, difficulty="medium")
    query = pair(witness)
    reasons = GEN.lesson_identifiable(canonical, query)
    assert len(reasons) >= 4
    assert GEN.lesson_identifiable([query, query, *canonical[:2]], query) == []


def test_retained_racket_counterexample_refutes_unseen_orientation_shortcut():
    import json

    path = TASK_HOME / "counterexamples" / "unseen_bottom_left.json"
    row = json.loads(path.read_text())
    grid = row["input"]
    assert row["task_id"] == TASK
    assert row["rule_hash"] == GEN.RULE_HASH
    assert observed(grid)["orientation"] == 2
    assert GEN.self_check(grid) == []
    assert expected_outline(grid) == row["racket_output"]
    assert GEN.CANONICAL_SHORTCUTS["canonical_orientations_only"](grid) == row["rival_output"]
    assert row["rival_output"] != row["racket_output"]


def test_reusable_schedule_probe_checks_every_declared_start_and_holdout():
    probe_path = TASK_HOME / "workspace" / "probe_schedule.py"
    spec = importlib.util.spec_from_file_location("rectangle_schedule_probe", probe_path)
    probe = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(probe)
    report = probe.run_probe(seeds=[0, 1], bands=["easy"])
    assert report["period"] == GEN.LESSON_SCHEDULE_PERIOD
    assert report["lessons"] == 8
    assert report["rotations"] == 40
    assert report["failures"] == []
