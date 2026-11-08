"""Focused semantic and regression tests for generator a76216bfa3e8."""
from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import numpy as np
import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK = "a76216bfa3e8"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = find_root(__file__)


def _authority_path(relative: str) -> Path:
    for prefix in ("", "shared/"):
        candidate = ROOT / f"{prefix}{relative}"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"missing authority {relative} under {ROOT}")


TRAIN_AUTHORITY = _authority_path(
    "data/base/solutions/training/92e50de0__a76216bfa3e8.json"
)
AUG_AUTHORITY = _authority_path(
    "data/base/solutions/augmented/92e50de0__5106f234d21b.json"
)
BANDS = ("easy", "medium", "hard")


def _canonical_rows():
    rows = []
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            rows.append(row)
    assert rows
    return rows


def _canonical_pairs():
    return canonical_pairs(TASK, root=ROOT)


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_authority_and_all_canonical_pairs():
    rows = _canonical_rows()
    selected = json.loads(TRAIN_AUTHORITY.read_text())["racket_target"]["target_code"]
    augmented = json.loads(AUG_AUTHORITY.read_text())["racket_target"]
    assert GEN.RULE_HASH == "33baf0d7ad4c"
    assert all(row["program_solution"] == selected for row in rows)
    assert augmented["target_code"] == selected
    assert augmented["raw_code"] != selected  # archival spelling remains preserved

    pairs = _canonical_pairs()
    assert len(pairs) == 8
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == before


def test_exact_override_boundaries_and_structured_incompatibilities():
    cases = [
        {
            "n_cell_rows": 8,
            "n_cell_cols": 8,
            "tail_h": 2,
            "tail_w": 2,
            "line_color": 9,
            "marker_color": 1,
            "marker_row_parity": 1,
            "marker_col_parity": 0,
            "marker_pattern": "skew4",
        },
        {"n_cell_rows": 8},
        {"tail_h": 3},
        {"n_cell_cols": 8},
        {"tail_w": 3},
    ]
    for band in BANDS:
        for index, overrides in enumerate(cases):
            grid = GEN.generate(81000 + index, 17 + index, difficulty=band, **overrides)
            observed = GEN.observe_overrides(grid)
            assert GEN.self_check(grid) == []
            assert all(observed[key] == value for key, value in overrides.items())

    for overrides, message in [
        ({"n_cell_rows": 8, "tail_h": 3}, "30-row"),
        ({"n_cell_cols": 8, "tail_w": 3}, "30-column"),
        ({"line_color": 4, "marker_color": 4}, "distinct"),
    ]:
        with pytest.raises(ValueError, match=message) as caught:
            GEN.generate(1, 0, difficulty="medium", **overrides)
        assert set(caught.value.incompatible_axes) == set(overrides)

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=7)


def test_self_check_rejects_targeted_mutations():
    grid = GEN.generate(9001, 2, difficulty="medium")
    info = GEN._analysis(grid)
    assert not info["errors"]

    mutations = {}

    separator_hole = copy.deepcopy(grid)
    separator_hole[info["line_rows"][0]][0] = 0
    mutations["separator_hole"] = separator_hole

    stray_line = copy.deepcopy(grid)
    row0, col0 = info["row_bounds"][0][0], info["col_bounds"][0][0]
    if (row0, col0) in info["marker_positions"]:
        col0 += 1
    stray_line[row0][col0] = info["line_color"]
    mutations["stray_line_color"] = stray_line

    second_marker_cell = copy.deepcopy(grid)
    target_cell = next(
        (r, c)
        for r, (rs, re) in enumerate(info["row_bounds"])
        for c, (cs, ce) in enumerate(info["col_bounds"])
        if (r, c) != (info["marker_row"], info["marker_col"])
        and re - rs + 1 == 3
        and ce - cs + 1 == 3
    )
    trs = info["row_bounds"][target_cell[0]][0]
    tcs = info["col_bounds"][target_cell[1]][0]
    for dr, dc in info["marker_offsets"]:
        second_marker_cell[trs + dr][tcs + dc] = info["marker_color"]
    mutations["second_marker_cell"] = second_marker_cell

    unsupported_pattern = copy.deepcopy(grid)
    for row, col in info["marker_positions"]:
        unsupported_pattern[row][col] = 0
    srs = info["row_bounds"][info["marker_row"]][0]
    scs = info["col_bounds"][info["marker_col"]][0]
    unsupported_pattern[srs + 1][scs + 1] = info["marker_color"]
    mutations["unsupported_marker_pattern"] = unsupported_pattern

    fresh_third_color = copy.deepcopy(grid)
    third = next(color for color in range(1, 10) if color not in {info["line_color"], info["marker_color"]})
    fresh_third_color[0][0] = third
    mutations["negative_recombination_fresh_color"] = fresh_third_color

    for name, mutated in mutations.items():
        assert GEN.self_check(mutated), name

    # Oracle executability for this rejected recombination is audited through
    # the real Racket bridge in the returned negative-recombination evidence.


def test_four_demo_lesson_refutes_all_named_rivals():
    demos = []
    for sample_index in range(4):
        grid = GEN.generate(12000, sample_index, difficulty="medium")
        demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
    query_grid = GEN.generate(12000, 7, difficulty="hard")
    query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}

    assert [
        GEN.schedule_profile(0, i) for i in range(GEN.LESSON_SCHEDULE_PERIOD)
    ] == list(GEN.SCHEDULE_PROFILES)
    assert GEN.lesson_identifiable(demos, query) == []
    assert {
        (GEN._analysis(pair["input"])["marker_row_parity"],
         GEN._analysis(pair["input"])["marker_col_parity"])
        for pair in demos
    } == {(0, 0), (0, 1), (1, 0), (1, 1)}
    for name, rival in GEN.LESSON_COMPETITORS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def _crosses_both_parity_axes(parities):
    return any(
        row_a != row_b and col_a != col_b
        for row_a, col_a in parities
        for row_b, col_b in parities
    )


def test_every_default_lesson_window_repeats_a_morphology_across_both_parity_axes():
    period = getattr(GEN, "LESSON_SCHEDULE_PERIOD", len(GEN.SCHEDULE_PROFILES))
    for band in BANDS:
        for start in range(period):
            parities_by_pattern = {}
            for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
                info = GEN._analysis(
                    GEN.generate(271828, sample_index, difficulty=band)
                )
                parities_by_pattern.setdefault(info["marker_pattern"], set()).add(
                    (info["marker_row_parity"], info["marker_col_parity"])
                )
            assert any(
                _crosses_both_parity_axes(parities)
                for parities in parities_by_pattern.values()
            ), (band, start, parities_by_pattern)


def test_default_seed_rotation_reaches_every_marker_morphology():
    observed = {
        GEN._analysis(GEN.generate(seed, 0, difficulty="medium"))["marker_pattern"]
        for seed in range(len(GEN._PATTERN_NAMES))
    }
    assert observed == set(GEN._PATTERN_NAMES)


def test_lesson_hook_rejects_morphology_to_parity_shortcut():
    patterns = GEN._PATTERN_NAMES[:4]
    parities = ((0, 0), (0, 1), (1, 0), (1, 1))
    demos = []
    for sample_index, (pattern, (row_parity, col_parity)) in enumerate(
        zip(patterns, parities)
    ):
        grid = GEN.generate(314159, sample_index, difficulty="medium",
                            marker_pattern=pattern,
                            marker_row_parity=row_parity,
                            marker_col_parity=col_parity)
        demos.append({"input": grid, "output": GEN.rule_mirror(grid)})

    query_grid = GEN.generate(314159, 8, difficulty="medium",
                              marker_pattern=patterns[0],
                              marker_row_parity=1,
                              marker_col_parity=1)
    errors = GEN.lesson_identifiable(
        demos, {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
    )
    assert any("morphology" in error and "parity" in error for error in errors)


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(20260726)
    py_state = random.getstate()
    np.random.seed(20260726)
    np_state = np.random.get_state()

    first = GEN.generate(123456, 789, difficulty="hard")
    assert random.getstate() == py_state
    after_np = np.random.get_state()
    assert after_np[0] == np_state[0]
    assert np.array_equal(after_np[1], np_state[1])
    assert after_np[2:] == np_state[2:]

    second = GEN.generate(123456, 789, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    frozen = _freeze(second)
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert _freeze(GEN.generate(123456, 789, difficulty="hard")) == frozen
