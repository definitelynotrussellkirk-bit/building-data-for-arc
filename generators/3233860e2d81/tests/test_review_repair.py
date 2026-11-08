"""Regression tests for the 2026-10-20 review repair."""
from __future__ import annotations

from collections import Counter
import importlib.util
from pathlib import Path
import sys

import pytest

from reviewer_support import find_root, load_selected_generator


TASK_ID = "3233860e2d81"
ROOT = find_root(__file__)
GEN, _SOURCE, _SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _component_sizes(grid, color):
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, column)
        for row in range(height)
        for column in range(width)
        if grid[row][column] == color
    }
    sizes = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        todo = [start]
        size = 0
        while todo:
            row, column = todo.pop()
            size += 1
            for point in (
                (row - 1, column),
                (row + 1, column),
                (row, column - 1),
                (row, column + 1),
            ):
                if point in remaining:
                    remaining.remove(point)
                    todo.append(point)
        sizes.append(size)
    return sorted(sizes, reverse=True)


@pytest.mark.parametrize("bad_seed", (True, False, 1.0, 1.75, "1"))
def test_public_api_rejects_nonliteral_integer_seed(bad_seed):
    with pytest.raises(TypeError, match="seed must be an integer"):
        GEN.generate(bad_seed, 0, difficulty="easy")


@pytest.mark.parametrize("bad_index", (True, False, 1.0, 1.75, "1"))
def test_public_api_rejects_nonliteral_integer_sample_index(bad_index):
    with pytest.raises(TypeError, match="sample_index must be an integer"):
        GEN.generate(17, bad_index, difficulty="easy")


def test_public_api_rejects_negative_sample_index():
    with pytest.raises(ValueError, match="sample_index must be non-negative"):
        GEN.generate(17, -1, difficulty="easy")


@pytest.mark.parametrize("difficulty", (True, False, 0, 1.0, "unknown"))
def test_public_api_rejects_unknown_difficulty(difficulty):
    with pytest.raises((TypeError, ValueError), match="difficulty"):
        GEN.generate(17, 0, difficulty=difficulty)


@pytest.mark.parametrize(
    ("axis", "bad_value"),
    (
        ("grid_h", True),
        ("grid_h", 12.0),
        ("grid_h", "12"),
        ("grid_w", False),
        ("n_colors", 4.0),
        ("min_count", "2"),
        ("min_count_gap", True),
        ("count_distribution", 1),
        ("count_distribution", "not-a-profile"),
    ),
)
def test_exact_overrides_reject_wrong_scalar_types_and_values(axis, bad_value):
    with pytest.raises((TypeError, ValueError), match=axis):
        GEN.generate(17, 0, difficulty="medium", **{axis: bad_value})


def test_none_overrides_are_equivalent_to_omitting_them():
    controls = {name: None for name in GEN.AXES}
    for difficulty in (None, "easy", "medium", "hard"):
        assert GEN.generate(37, 6, difficulty=difficulty, **controls) == GEN.generate(
            37, 6, difficulty=difficulty
        )


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_joint_dimension_selection_honors_narrow_width_and_color_count(difficulty):
    grid = GEN.generate(0, 3, difficulty=difficulty, grid_w=5, n_colors=7)
    observed = GEN.observe_overrides(grid)
    assert observed["grid_w"] == 5
    assert observed["n_colors"] == 7
    assert GEN.self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": {"grid_w": 5, "n_colors": 7}},
    ) == []


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_minimum_declared_shape_remains_realizable_in_every_band(difficulty):
    grid = GEN.generate(0, 3, difficulty=difficulty, grid_h=5, grid_w=5)
    assert (len(grid), len(grid[0])) == (5, 5)
    assert GEN.self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": {"grid_h": 5, "grid_w": 5}},
    ) == []


@pytest.mark.parametrize(
    "distribution", ("ascending", "tight_spread", "wide_spread")
)
def test_three_color_distribution_override_is_observable(distribution):
    grid = GEN.generate(13, 3, difficulty="medium", n_colors=3,
                        count_distribution=distribution)
    observed = GEN.observe_overrides(grid)
    assert observed["n_colors"] == 3
    assert observed["count_distribution"] == distribution


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_canonical_profile_schedule_has_exact_support_in_every_band(difficulty):
    for sample_index in (0, 8, 12):
        grid = GEN.generate(71, sample_index, difficulty=difficulty)
        assert (len(grid), len(grid[0])) == (12, 12)
        counts = Counter(value for row in grid for value in row if value)
        assert len(counts) == 3
        assert len({value for row in grid for value in row}) == 4
        assert GEN.self_check(grid) == []


def test_broad_schedule_keeps_top_three_as_a_selection():
    grid = GEN.generate(71, 5, difficulty="medium")
    counts = Counter(value for row in grid for value in row if value)
    assert 4 <= len(counts) <= 7
    assert len(GEN.expected_output(grid)) == 3


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_generated_inputs_refute_largest_connected_component_ranking(difficulty):
    for sample_index in range(12):
        grid = GEN.generate(940_000 + sample_index, sample_index, difficulty=difficulty)
        counts = Counter(value for row in grid for value in row if value)
        intended = GEN.expected_output(grid)
        rival = GEN.SEMANTIC_RIVALS["largest_component"](grid)
        top_color = intended[0][0]
        runner_up_total = counts[intended[1][0]]
        top_components = _component_sizes(grid, top_color)
        assert 2 <= len(top_components) <= 3
        assert max(top_components) < runner_up_total
        assert rival != intended
        assert GEN.SEMANTIC_WITNESSES["total_count_not_largest_component"](grid)


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_fragmentation_is_not_a_unique_marker_for_the_winning_color(difficulty):
    for sample_index in range(12):
        grid = GEN.generate(950_000 + sample_index, sample_index, difficulty=difficulty)
        intended = GEN.expected_output(grid)
        top_color = intended[0][0]
        colors = {value for row in grid for value in row if value}
        fragmented = {
            color for color in colors if len(_component_sizes(grid, color)) > 1
        }
        assert top_color in fragmented
        assert fragmented - {top_color}


def test_declared_fragmentation_rival_is_refuted_by_generated_inputs():
    rival = GEN.SEMANTIC_RIVALS["fragment_count_then_size"]
    witness = GEN.SEMANTIC_WITNESSES["total_count_not_fragment_count"]
    for sample_index in range(12):
        grid = GEN.generate(960_000 + sample_index, sample_index, difficulty="medium")
        assert rival(grid) != GEN.expected_output(grid)
        assert witness(grid)


def test_lesson_contract_refutes_declared_competitor_in_every_rotation():
    grids = [GEN.generate(991, index, difficulty="hard") for index in range(4)]
    pairs = [{"input": grid, "output": GEN.expected_output(grid)} for grid in grids]
    assert GEN.EXAMPLES_NEEDED == 3
    for query_index in range(4):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        query = pairs[query_index]
        assert GEN.lesson_identifiable(demos, query) == []
        rival = GEN.LESSON_COMPETITORS["largest_component"]
        assert any(rival(pair["input"]) != pair["output"] for pair in demos)


def test_override_matrix_probe_is_portable_and_covers_shared_cases():
    path = ROOT / "generators" / TASK_ID / "workspace" / "probe_override_matrix.py"
    assert path.is_file()
    spec = importlib.util.spec_from_file_location("override_probe_3233860e2d81", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    report = module.probe(seed=0, sample_index=3, bands=("easy",))
    assert report["generator_sha256"] == _SOURCE_SHA256
    assert report["case_count"] == 705
    assert report["attempted"] == 705
    assert report["accepted"] == 705
    assert report["rejected"] == 0
    assert report["failure_count"] == 0


def test_top_k_parametric_prototype_is_task_local_and_preserves_original_rule():
    path = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
    assert path.is_file()
    spec = importlib.util.spec_from_file_location("top_k_parametric_3233860e2d81", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    assert module.TOP_K_VALUES == (2, 3, 4)
    assert module.instantiate_rule(3) == module.canonical_rule(root=ROOT)
    assert module.instantiate_rule(2) != module.instantiate_rule(4)
    for bad in (True, 3.0, "3", 1, 5):
        with pytest.raises((TypeError, ValueError)):
            module.instantiate_rule(bad)

    inputs = module.generate_inputs(17)
    assert len(inputs) == 4
    assert len({str(grid) for grid in inputs}) == 4
    assert all(len({value for row in grid for value in row if value}) >= 4 for grid in inputs)
