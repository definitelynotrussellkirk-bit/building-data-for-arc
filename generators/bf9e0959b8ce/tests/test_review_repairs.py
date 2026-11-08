from __future__ import annotations

import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "bf9e0959b8ce"
ROOT = find_root(__file__)
GEN, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


@pytest.mark.parametrize(
    ("axis", "value"),
    [
        ("grid_h", True),
        ("grid_h", 12.5),
        ("grid_h", "12"),
        ("grid_w", False),
        ("grid_w", 14.5),
        ("grid_w", "14"),
        ("n_dots", True),
        ("n_dots", 4.5),
        ("n_dots", "4"),
    ],
)
def test_integer_override_axes_reject_coercible_non_integer_scalars(axis, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(20261019, 5, difficulty="hard", **{axis: value})


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1", None])
def test_seed_is_a_strict_integer(seed):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, -1, 1.0, 1.75, "1", None])
def test_sample_index_is_a_nonnegative_strict_integer(sample_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, sample_index)


@pytest.mark.parametrize(
    "difficulty", [True, False, 0, 1.0, "__invalid_difficulty__"]
)
def test_difficulty_is_none_or_a_named_band(difficulty):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, difficulty=difficulty)


def test_single_source_line_shortcut_fits_every_labeled_canonical_pair():
    shortcut = GEN.CANONICAL_SHORTCUTS["single_source_line"]
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert pairs
    for pair in pairs:
        assert shortcut(pair["input"]) == pair["output"]


def _motion_axis_coordinates(grid):
    info = GEN._analysis(grid)
    assert info["errors"] == []
    if info["orientation"] == "row":
        return [row for row, _, _ in info["dots"]]
    return [col for _, col, _ in info["dots"]]


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_generated_inputs_refute_single_source_line_shortcut(difficulty):
    shortcut = GEN.CANONICAL_SHORTCUTS["single_source_line"]
    for sample_index in range(24):
        grid = GEN.generate(8675309, sample_index, difficulty=difficulty)
        assert len(set(_motion_axis_coordinates(grid))) >= 2
        assert shortcut(grid) != GEN.rule_mirror(grid)


def test_retained_single_source_line_counterexample_replays_exactly():
    path = (
        ROOT
        / "generators"
        / TASK_ID
        / "counterexamples"
        / "single-source-line.json"
    )
    payload = json.loads(path.read_text())
    grid = payload["input"]
    shortcut = GEN.CANONICAL_SHORTCUTS["single_source_line"]
    assert GEN.self_check(grid) == []
    assert GEN.rule_mirror(grid) == payload["intended_output"]
    assert shortcut(grid) == payload["shortcut_output"]
    assert payload["intended_output"] != payload["shortcut_output"]
    assert payload["generator_source_sha256"] == SOURCE_SHA256


def test_every_cyclic_three_demo_window_refutes_all_declared_competitors():
    for start in range(18):
        demos = []
        for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
            grid = GEN.generate(7717, sample_index, difficulty="medium")
            demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
        query_grid = GEN.generate(
            7717, start + GEN.EXAMPLES_NEEDED, difficulty="medium"
        )
        query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
        assert GEN.lesson_identifiable(demos, query) == []
        for name, competitor in GEN.LESSON_COMPETITORS.items():
            assert any(
                competitor(demo["input"]) != demo["output"] for demo in demos
            ), (start, name)


def test_every_query_rotation_of_each_cyclic_lesson_refutes_all_competitors():
    """Any one of the four materialized pairs can be held out as query."""
    for start in range(18):
        pairs = []
        for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
            grid = GEN.generate(7717, sample_index, difficulty="medium")
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, query) == [], (start, query_index)
            for name, competitor in GEN.LESSON_COMPETITORS.items():
                assert any(
                    competitor(demo["input"]) != demo["output"]
                    for demo in demos
                ), (start, query_index, name)
