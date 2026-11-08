"""Semantic and contract regressions for generator b0e266482663."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

TASK_ID = "b0e266482663"
TASK_DIR = Path(__file__).resolve().parents[1]
REPO = TASK_DIR.parents[1]
sys.path.insert(0, str(REPO / "shared" / "runtime"))
SPEC = importlib.util.spec_from_file_location(
    f"review_{TASK_ID}_generator", TASK_DIR / "generator.py"
)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _canonical_row() -> dict:
    with (REPO / "shared" / "data" / "canonical" / "puzzles.jsonl").open(
        encoding="utf-8"
    ) as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _pairs() -> list[dict]:
    row = _canonical_row()
    return [*row["train"], *row["test"]]


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def _features(grid) -> dict[str, object]:
    height, width = len(grid), len(grid[0])
    row_shooters = {r for r in range(1, height) if grid[r][0] == 2}
    col_shooters = {c for c in range(1, width) if grid[0][c] == 3}
    blockers = {
        (r, c)
        for r in range(1, height)
        for c in range(1, width)
        if grid[r][c] == 9
    }
    active_h = {
        (r, c)
        for r, c in blockers
        if r in row_shooters
        and c < width - 1
        and all(grid[r][cc] != 9 for cc in range(1, c))
    }
    active_v = {
        (r, c)
        for r, c in blockers
        if c in col_shooters
        and r < height - 1
        and all(grid[rr][c] != 9 for rr in range(1, r))
    }
    first_h = {(r, c) for r, c in active_h if c == 1}
    first_v = {(r, c) for r, c in active_v if r == 1}
    counts = {"h_only": 0, "v_only": 0, "both": 0}
    for r in range(1, height):
        for c in range(1, width):
            if grid[r][c] == 9:
                continue
            h_ray = r in row_shooters and all(
                grid[r][cc] != 9 for cc in range(1, c + 1)
            )
            v_ray = c in col_shooters and all(
                grid[rr][c] != 9 for rr in range(1, r + 1)
            )
            if h_ray and v_ray:
                counts["both"] += 1
            elif h_ray:
                counts["h_only"] += 1
            elif v_ray:
                counts["v_only"] += 1
    return {
        "row_shooters": row_shooters,
        "col_shooters": col_shooters,
        "blockers": blockers,
        "active_h": active_h,
        "active_v": active_v,
        "first_h": first_h,
        "first_v": first_v,
        **counts,
    }




def _visible_stop_counts(grid) -> tuple[int, int]:
    """Count first blockers whose suffix still exposes stopped background."""
    feature = _features(grid)
    horizontal = sum(
        any(grid[row][later] != 9 for later in range(col + 1, len(grid[0])))
        for row, col in feature["active_h"]
    )
    vertical = sum(
        any(grid[later][col] != 9 for later in range(row + 1, len(grid)))
        for row, col in feature["active_v"]
    )
    return horizontal, vertical

def test_rule_pin_canonical_pairs_and_python_mirror_are_exact():
    assert GEN.VERSION == "4.6.0"
    assert GEN.RULE_HASH == "d12310adc715"
    assert len(_pairs()) == 3
    for pair in _pairs():
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_public_axes_are_exact_observable_and_band_safe_at_boundaries():
    expected_axes = {
        "grid_h",
        "grid_w",
        "n_row_shoot",
        "n_col_shoot",
        "n_blockers",
    }
    assert set(GEN.AXES) == expected_axes
    cases = (
        {
            "grid_h": 6,
            "grid_w": 6,
            "n_row_shoot": 1,
            "n_col_shoot": 1,
            "n_blockers": 2,
        },
        {
            "grid_h": 13,
            "grid_w": 14,
            "n_row_shoot": 4,
            "n_col_shoot": 4,
            "n_blockers": 10,
        },
        {
            "grid_h": 7,
            "grid_w": 8,
            "n_row_shoot": 2,
            "n_col_shoot": 2,
            "n_blockers": 3,
        },
    )
    for difficulty in ("easy", "medium", "hard"):
        for index, requested in enumerate(cases):
            grid = GEN.generate(
                1000 + index, 20 + index, difficulty=difficulty, **requested
            )
            assert GEN.self_check(grid, difficulty=difficulty) == []
            assert GEN.observe_overrides(grid) == requested

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, typo_axis=7)


def test_default_census_teaches_both_stops_adjacent_origins_and_first_steps():
    canonical_shapes = {(7, 8), (8, 9), (9, 10)}
    for band_index, difficulty in enumerate(("easy", "medium", "hard")):
        rows = []
        seen = set()
        canonical_shape_hits = 0
        for sample_index in range(160):
            grid = GEN.generate(
                50_000 + 1000 * band_index + sample_index,
                sample_index,
                difficulty=difficulty,
            )
            assert GEN.self_check(grid, difficulty=difficulty) == []
            feature = _features(grid)
            rows.append(feature)
            seen.add(_freeze(grid))
            canonical_shape_hits += (len(grid), len(grid[0])) in canonical_shapes
            assert feature["active_h"], "horizontal stop branch hidden"
            assert feature["active_v"], "vertical stop branch hidden"
            assert feature["h_only"] > 0
            assert feature["v_only"] > 0
            assert feature["both"] > 0

        assert sum(1 in row["row_shooters"] for row in rows) >= 30
        assert sum(1 in row["col_shooters"] for row in rows) >= 30
        assert sum(bool(row["first_h"]) for row in rows) >= 25
        assert sum(bool(row["first_v"]) for row in rows) >= 25
        assert canonical_shape_hits >= 45
        assert len(seen) >= 155


def test_three_example_schedule_covers_witnesses_and_refutes_every_rival():
    grids = [GEN.generate(81_001, index, difficulty="medium") for index in range(4)]
    assert [GEN.schedule_profile(81_001, index, "medium") for index in range(3)] == list(
        GEN.SCHEDULE_PROFILES
    )
    for name, witness in GEN.SEMANTIC_WITNESSES.items():
        assert any(witness(grid) for grid in grids[:3]), name

    lesson = [{"input": grid, "output": GEN.rule_mirror(grid)} for grid in grids]
    assert GEN.lesson_identifiable(lesson[:3], lesson[3]) == []
    for rival_name, rival in GEN.SEMANTIC_RIVALS.items():
        assert any(
            rival(pair["input"]) != pair["output"] for pair in lesson[:3]
        ), rival_name


def test_every_three_consecutive_examples_form_an_identifiable_lesson():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(12):
            grids = [
                GEN.generate(91_001, start + offset, difficulty=difficulty)
                for offset in range(4)
            ]
            pairs = [
                {"input": grid, "output": GEN.rule_mirror(grid)} for grid in grids
            ]
            assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == [], (
                difficulty,
                start,
                [
                    GEN.schedule_profile(91_001, start + offset, difficulty)
                    for offset in range(4)
                ],
            )


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20261002)
    state = random.getstate()
    first = GEN.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert GEN.generate(123, 456, difficulty="hard") == second


def test_distribution_probe_classifies_semantic_features():
    probe_path = (
        REPO
        / "generators"
        / "b0e266482663"
        / "workspace"
        / "distribution_probe.py"
    )
    spec = importlib.util.spec_from_file_location("b0_distribution_probe", probe_path)
    probe = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(probe)

    grid = [
        [0, 3, 0, 0, 0, 0],
        [2, 0, 0, 9, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 9, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    features = probe.analyze_grid(grid)
    assert features == {
        "height": 6,
        "width": 6,
        "row_shooters": 1,
        "col_shooters": 1,
        "productive_row_shooters": 1,
        "productive_col_shooters": 1,
        "blockers": 2,
        "active_horizontal_stop": True,
        "active_vertical_stop": True,
        "adjacent_row_shooter": True,
        "adjacent_col_shooter": True,
        "first_step_horizontal_stop": False,
        "first_step_vertical_stop": False,
        "horizontal_only_cells": 1,
        "vertical_only_cells": 1,
        "crossing_cells": 1,
        "nonlowest_shooter_crossings": 0,
        "lowest_and_highest_row_stops": False,
        "lowest_and_highest_col_stops": False,
    }

    masked = [
        [0, 3, 0, 0, 0, 0],
        [2, 0, 0, 9, 9, 9],
        [0, 0, 0, 0, 0, 0],
        [0, 9, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    masked_features = probe.analyze_grid(masked)
    assert masked_features["active_horizontal_stop"] is False
    assert masked_features["first_step_horizontal_stop"] is False
    assert masked_features["active_vertical_stop"] is True

    shortcut_report = probe.shooter_shortcut_window_census(
        GEN, "easy", seed=83_000_006, starts=24
    )
    assert shortcut_report["checked"] == 24
    assert shortcut_report["failures"] == {}
    assert {
        "cyan_only_lowest_axes_horizontal",
        "cyan_only_lowest_axes_vertical",
        "first_three_rows_only",
        "last_three_rows_only",
        "first_three_cols_only",
        "last_three_cols_only",
        "first_three_rows_respect_blockers",
        "last_three_rows_respect_blockers",
        "first_three_cols_respect_blockers",
        "last_three_cols_respect_blockers",
    } <= set(shortcut_report["refuted"])
    assert all(count == 24 for count in shortcut_report["refuted"].values())

def test_self_check_rejects_a_stop_hidden_by_only_more_blockers():
    # This was emitted by the 4.0.0 default generator (easy, seed 7_000_025,
    # sample 25).  The first blocker on row 2 has no non-blocker cell after it,
    # so the output cannot reveal that the horizontal ray stopped there.
    grid = [
        [0, 3, 0, 0, 0, 3, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [2, 0, 0, 0, 0, 9, 9, 9],
        [0, 0, 0, 0, 9, 9, 0, 0],
        [2, 0, 0, 0, 0, 0, 0, 0],
        [0, 9, 0, 9, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 9, 9],
    ]
    assert any(
        "observable horizontal ray" in error for error in GEN.self_check(grid)
    )


def test_dense_generation_reserves_visible_suffixes_after_stopping_blockers():
    cases = (
        # Default counterexamples found by the round-two adversarial probe.
        (7_000_025, 25, "easy", {}),
        (7_000_010, 10, "medium", {}),
        (7_000_008, 8, "hard", {}),
        # Dense exact overrides stress each schedule profile at minimum shape.
        (
            1431,
            0,
            "hard",
            {
                "grid_h": 6,
                "grid_w": 6,
                "n_row_shoot": 4,
                "n_col_shoot": 4,
                "n_blockers": 10,
            },
        ),
        (
            478,
            1,
            "hard",
            {
                "grid_h": 6,
                "grid_w": 6,
                "n_row_shoot": 4,
                "n_col_shoot": 4,
                "n_blockers": 10,
            },
        ),
        (
            1554,
            2,
            "hard",
            {
                "grid_h": 6,
                "grid_w": 6,
                "n_row_shoot": 4,
                "n_col_shoot": 4,
                "n_blockers": 10,
            },
        ),
    )
    for seed, sample_index, difficulty, overrides in cases:
        grid = GEN.generate(
            seed, sample_index, difficulty=difficulty, **overrides
        )
        assert _visible_stop_counts(grid)[0] > 0, (seed, sample_index, grid)
        assert _visible_stop_counts(grid)[1] > 0, (seed, sample_index, grid)


def test_adjacent_profile_needs_only_two_anchor_blockers_for_first_step_stops():
    grid = GEN.generate(
        0,
        0,
        difficulty="medium",
        grid_h=6,
        grid_w=6,
        n_row_shoot=2,
        n_col_shoot=2,
        n_blockers=2,
    )
    feature = _features(grid)
    assert feature["first_h"], grid
    assert feature["first_v"], grid


def test_stop_before_blocker_rival_preserves_the_perpendicular_ray():
    grid = [
        [0, 0, 3, 3, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [2, 0, 0, 0, 9, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 9, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    assert GEN.self_check(grid) == []
    assert GEN.rule_mirror(grid)[2][3] == 8
    # The off-by-one horizontal ray no longer reaches this cell, but the
    # vertical ray still does, so a faithful rival leaves green rather than 0.
    assert GEN._rival_stop_before_blocker(grid)[2][3] == 3



def _rule_with_shooter_subset(grid, keep_rows, keep_cols):
    """Independent rival used to test whether every marker visibly matters."""
    height, width = len(grid), len(grid[0])
    rows = sorted(r for r in range(1, height) if grid[r][0] == 2)
    cols = sorted(c for c in range(1, width) if grid[0][c] == 3)
    active_rows = set(keep_rows(rows))
    active_cols = set(keep_cols(cols))
    output = [list(row) for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 9:
                continue
            horizontal = (
                col >= 1
                and row in active_rows
                and all(grid[row][cc] != 9 for cc in range(1, col + 1))
            )
            vertical = (
                row >= 1
                and col in active_cols
                and all(grid[rr][col] != 9 for rr in range(1, row + 1))
            )
            if horizontal and vertical:
                output[row][col] = 8
            elif horizontal:
                output[row][col] = 2
            elif vertical:
                output[row][col] = 3
    return output


def _rule_with_blocker_respect_subset(grid, respect_rows, respect_cols):
    """Independent rival where only selected shooters stop at blockers."""
    height, width = len(grid), len(grid[0])
    rows = sorted(r for r in range(1, height) if grid[r][0] == 2)
    cols = sorted(c for c in range(1, width) if grid[0][c] == 3)
    blocked_rows = set(respect_rows(rows))
    blocked_cols = set(respect_cols(cols))
    output = [list(row) for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 9:
                continue
            horizontal = (
                col >= 1
                and row in rows
                and (
                    row not in blocked_rows
                    or all(grid[row][cc] != 9 for cc in range(1, col + 1))
                )
            )
            vertical = (
                row >= 1
                and col in cols
                and (
                    col not in blocked_cols
                    or all(grid[rr][col] != 9 for rr in range(1, row + 1))
                )
            )
            if horizontal and vertical:
                output[row][col] = 8
            elif horizontal:
                output[row][col] = 2
            elif vertical:
                output[row][col] = 3
    return output


def test_easy_curriculum_refutes_lowest_shooter_only_on_each_axis():
    # Version 4.1.0 counterexample: all secondary edge markers in this window
    # are either absent or blocked at their first interior cell, so a solver can
    # treat only the lowest-coordinate shooter on each edge as active.
    seed = 83_000_019
    start = 19
    demos = []
    for offset in range(3):
        grid = GEN.generate(seed, start + offset, difficulty="easy")
        demos.append((grid, GEN.rule_mirror(grid)))

    keep_lowest = lambda values: values[:1]
    keep_all = lambda values: values
    assert any(
        _rule_with_shooter_subset(grid, keep_lowest, keep_all) != output
        for grid, output in demos
    )
    assert any(
        _rule_with_shooter_subset(grid, keep_all, keep_lowest) != output
        for grid, output in demos
    )


def test_separated_profile_exposes_two_productive_shooters_per_axis():
    # Every default three-example lesson contains one separated profile.  It is
    # the source-like fixture that must prove more than one marker on each edge
    # emits a ray; the adjacent profile deliberately blocks its second markers.
    for difficulty in ("easy", "medium", "hard"):
        for index in range(60):
            sample_index = 3 * index + 1
            assert GEN.schedule_profile(5_000_000 + index, sample_index, difficulty) == (
                "separated_stops"
            )
            grid = GEN.generate(
                5_000_000 + index,
                sample_index,
                difficulty=difficulty,
            )
            feature = _features(grid)
            productive_rows = sum(grid[row][1] != 9 for row in feature["row_shooters"])
            productive_cols = sum(grid[1][col] != 9 for col in feature["col_shooters"])
            assert productive_rows >= 2, (difficulty, index, grid)
            assert productive_cols >= 2, (difficulty, index, grid)


def test_easy_curriculum_refutes_first_two_shooters_only_on_each_axis():
    # Version 4.2.0 counterexample: all three demonstrations use at most two
    # productive markers per edge, so an "only the first two markers shoot"
    # shortcut is observationally identical to the real rule.
    seed = 83_000_006
    start = 6
    demos = []
    for offset in range(3):
        grid = GEN.generate(seed, start + offset, difficulty="easy")
        demos.append((grid, GEN.rule_mirror(grid)))

    keep_first_two = lambda values: values[:2]
    keep_all = lambda values: values
    assert any(
        _rule_with_shooter_subset(grid, keep_first_two, keep_all) != output
        for grid, output in demos
    )
    assert any(
        _rule_with_shooter_subset(grid, keep_all, keep_first_two) != output
        for grid, output in demos
    )


def test_easy_curriculum_refutes_first_three_shooters_only_on_each_axis():
    # Version 4.4.0 counterexample: the public axis allows four markers, but
    # this three-example window never needs a fourth one.  A solver can cap the
    # quantified rule at three shooters and still match every demonstration.
    seed = 113_000_000
    start = 0
    demos = []
    for offset in range(3):
        grid = GEN.generate(seed, start + offset, difficulty="easy")
        demos.append((grid, GEN.rule_mirror(grid)))

    keep_first_three = lambda values: values[:3]
    keep_all = lambda values: values
    assert any(
        _rule_with_shooter_subset(grid, keep_first_three, keep_all) != output
        for grid, output in demos
    )
    assert any(
        _rule_with_shooter_subset(grid, keep_all, keep_first_three) != output
        for grid, output in demos
    )


def test_late_profile_exposes_four_productive_shooters_per_axis():
    # The third curriculum slot is the maximum-cardinality generalization
    # fixture.  It must visibly exercise every legal marker on each edge so the
    # learned rule quantifies over markers instead of memorizing any fixed cap.
    for difficulty in ("easy", "medium", "hard"):
        for index in range(60):
            sample_index = 3 * index + 2
            assert GEN.schedule_profile(6_000_000 + index, sample_index, difficulty) == (
                "late_stops"
            )
            grid = GEN.generate(
                6_000_000 + index,
                sample_index,
                difficulty=difficulty,
            )
            feature = _features(grid)
            productive_rows = sum(grid[row][1] != 9 for row in feature["row_shooters"])
            productive_cols = sum(grid[1][col] != 9 for col in feature["col_shooters"])
            assert productive_rows == 4, (difficulty, index, grid)
            assert productive_cols == 4, (difficulty, index, grid)


def test_curriculum_refutes_three_marker_blocker_scope_shortcuts():
    # Version 4.5.0 counterexamples: all four markers visibly emit, but a
    # dropped extreme marker need not meet a blocker.  A solver can therefore
    # apply blocking to only the first or last three markers and fit the lesson.
    keep_all = lambda values: values
    cases = (
        (123_000_000, 0, lambda values: values[:3], keep_all),
        (123_000_000, 0, lambda values: values[-3:], keep_all),
        (123_000_001, 1, keep_all, lambda values: values[:3]),
        (123_000_000, 0, keep_all, lambda values: values[-3:]),
    )
    for seed, start, respect_rows, respect_cols in cases:
        demos = []
        for offset in range(3):
            grid = GEN.generate(seed, start + offset, difficulty="easy")
            demos.append((grid, GEN.rule_mirror(grid)))
        assert any(
            _rule_with_blocker_respect_subset(
                grid, respect_rows, respect_cols
            )
            != output
            for grid, output in demos
        ), (seed, start)


def test_late_profile_stops_lowest_and_highest_shooters_on_both_axes():
    for difficulty in ("easy", "medium", "hard"):
        for index in range(60):
            sample_index = 3 * index + 2
            grid = GEN.generate(
                8_000_000 + index,
                sample_index,
                difficulty=difficulty,
            )
            feature = _features(grid)
            rows = sorted(feature["row_shooters"])
            cols = sorted(feature["col_shooters"])
            stopped_rows = {row for row, _ in feature["active_h"]}
            stopped_cols = {col for _, col in feature["active_v"]}
            assert {rows[0], rows[-1]} <= stopped_rows, (
                difficulty,
                index,
                grid,
            )
            assert {cols[0], cols[-1]} <= stopped_cols, (
                difficulty,
                index,
                grid,
            )


def _rival_cyan_only_on_lowest_shooter_axes(grid, fallback):
    """Independent rival: secondary-secondary crossings never become cyan."""
    height, width = len(grid), len(grid[0])
    rows = sorted(r for r in range(1, height) if grid[r][0] == 2)
    cols = sorted(c for c in range(1, width) if grid[0][c] == 3)
    output = [list(row) for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 9:
                continue
            horizontal = (
                col >= 1
                and row in rows
                and all(grid[row][cc] != 9 for cc in range(1, col + 1))
            )
            vertical = (
                row >= 1
                and col in cols
                and all(grid[rr][col] != 9 for rr in range(1, row + 1))
            )
            if horizontal and vertical:
                output[row][col] = (
                    8 if row == rows[0] or col == cols[0] else fallback
                )
            elif horizontal:
                output[row][col] = 2
            elif vertical:
                output[row][col] = 3
    return output


def _has_nonlowest_shooter_crossing(grid):
    height, width = len(grid), len(grid[0])
    rows = sorted(r for r in range(1, height) if grid[r][0] == 2)
    cols = sorted(c for c in range(1, width) if grid[0][c] == 3)
    if len(rows) < 2 or len(cols) < 2:
        return False
    for row in rows[1:]:
        for col in cols[1:]:
            horizontal = all(grid[row][cc] != 9 for cc in range(1, col + 1))
            vertical = all(grid[rr][col] != 9 for rr in range(1, row + 1))
            if horizontal and vertical:
                return True
    return False


def test_easy_curriculum_refutes_cyan_only_on_lowest_shooter_axes():
    # Version 4.3.0 counterexample: every actual crossing in this window touches
    # the lowest row shooter or the lowest column shooter.  Both fallback-color
    # variants therefore match the true outputs despite extra active markers.
    seed = 93_000_300
    start = 300
    demos = []
    for offset in range(3):
        grid = GEN.generate(seed, start + offset, difficulty="easy")
        demos.append((grid, GEN.rule_mirror(grid)))
    for fallback in (2, 3):
        assert any(
            _rival_cyan_only_on_lowest_shooter_axes(grid, fallback) != output
            for grid, output in demos
        )


def test_separated_profile_exposes_a_secondary_secondary_cyan_crossing():
    for difficulty in ("easy", "medium", "hard"):
        for index in range(60):
            sample_index = 3 * index + 1
            grid = GEN.generate(
                7_000_000 + index,
                sample_index,
                difficulty=difficulty,
            )
            assert _has_nonlowest_shooter_crossing(grid), (
                difficulty,
                index,
                grid,
            )
