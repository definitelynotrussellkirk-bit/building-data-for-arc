"""Regression contract for the 4fd85612056f generator repair.

These tests are intentionally source-tree portable: they bind canonical data and
runtime dependencies to the test file's own repository rather than cwd.
"""
from __future__ import annotations

from itertools import product
import copy

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

ROOT = find_root(__file__)

TASK_ID = "4fd85612056f"
GEN, _, _ = load_selected_generator(TASK_ID, root=ROOT)
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
CANONICAL_DIMS = {(8, 13), (11, 11), (10, 12), (9, 10), (8, 10)}
SHAPES = {"rectangle", "elbow", "tee", "cross"}
BANDS = (None, "easy", "medium", "hard")


def _component_heights(grid):
    return sorted((GEN._bbox(component)[0] for component in GEN._components(grid)), reverse=True)


def test_metadata_rule_hash_and_public_axes_are_pinned():
    assert GEN.GENERATOR_ID == TASK_ID == GEN.TASK_ID
    assert GEN.RULE_HASH == "2ea4086e36a6"
    assert set(GEN.AXES) == {"grid_h", "grid_w", "target_shape"}
    assert GEN.LESSON_SCHEDULE_PERIOD == 10
    assert GEN.EXAMPLES_NEEDED == 4


def test_all_canonical_pairs_are_accepted_and_mirrored_exactly():
    assert len(PAIRS) == 5
    for pair in PAIRS:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN._intended_output(source) == pair["output"]
        assert source == pair["input"]
        assert (len(source), len(source[0])) in CANONICAL_DIMS
        assert _component_heights(source) == [3, 2, 1]


def test_strongest_canonical_shortcut_really_fits_every_labeled_pair():
    rival = GEN.CANONICAL_SHORTCUTS["same_color_components"]
    assert all(rival(pair["input"]) == pair["output"] for pair in PAIRS)


@pytest.mark.parametrize("band", BANDS)
def test_default_population_is_lawful_observable_and_counterexample_rich(band):
    seen = set()
    shapes = set()
    dimensions = set()
    answer_color_counts = set()
    for sample_index in range(30):
        grid = GEN.generate(731, sample_index, difficulty=band)
        assert grid == GEN.generate(731, sample_index, difficulty=band)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        observed = GEN.observe_overrides(grid)
        assert set(observed) == set(GEN.AXES)
        assert observed["grid_h"] == len(grid)
        assert observed["grid_w"] == len(grid[0])
        assert observed["target_shape"] in SHAPES
        assert _component_heights(grid) == [3, 2, 1]
        assert len({cell for row in grid for cell in row}) == 4
        answer = GEN._intended_output(grid)
        answer_colors = len({cell for row in answer for cell in row if cell})
        answer_color_counts.add(answer_colors)
        if answer_colors == 2:
            assert GEN.SEMANTIC_RIVALS["same_color_components"](grid) != answer
        else:
            assert answer_colors == 1
            assert GEN.SEMANTIC_RIVALS["same_color_components"](grid) == answer
        for name in (
            "largest_cell_count",
            "widest_component",
            "leftmost_component",
            "first_nonrectangular",
        ):
            assert GEN.SEMANTIC_RIVALS[name](grid) != answer, (band, sample_index, name)
        dimensions.add((len(grid), len(grid[0])))
        shapes.add(observed["target_shape"])
        seen.add(tuple(map(tuple, grid)))
    assert CANONICAL_DIMS <= dimensions
    assert shapes == SHAPES
    assert answer_color_counts == {1, 2}
    assert len(seen) >= 28


def test_difficulty_band_participates_without_changing_the_rule():
    grids = [GEN.generate(8128, 3, difficulty=band) for band in ("easy", "medium", "hard")]
    assert len({tuple(map(tuple, grid)) for grid in grids}) == 3
    assert all(GEN.self_check(grid) == [] for grid in grids)
    assert len({tuple(map(tuple, GEN._intended_output(grid))) for grid in grids}) == 3


def test_mutation_fixture_hook_uses_named_pairs_and_all_are_rejected():
    fixtures = list(GEN.mutation_fixtures())
    assert fixtures
    assert all(isinstance(name, str) and GEN.self_check(grid) for name, grid in fixtures)


@pytest.mark.parametrize("band", BANDS)
def test_exact_axes_work_at_crossed_boundaries(band):
    for height, width, shape in product((8, 11), (10, 13), sorted(SHAPES)):
        requested = {"grid_h": height, "grid_w": width, "target_shape": shape}
        for sample_index in (0, 1):
            grid = GEN.generate(991, sample_index, difficulty=band, **requested)
            assert GEN.self_check(grid) == []
            assert GEN.observe_overrides(grid) == requested
            assert grid == GEN.generate(991, sample_index, difficulty=band, **requested)


@pytest.mark.parametrize("name", ("grid_h", "grid_w"))
@pytest.mark.parametrize("value", (True, 9.0, "9", -1, 99))
def test_invalid_integer_overrides_fail_loudly(name, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **{name: value})


@pytest.mark.parametrize("value", (True, 1, "triangle", "", object()))
def test_invalid_shape_overrides_fail_loudly(value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, target_shape=value)


@pytest.mark.parametrize(
    "args, kwargs",
    (
        ((True, 0), {}),
        ((1.0, 0), {}),
        (("1", 0), {}),
        ((0, True), {}),
        ((0, -1), {}),
        ((0, 0), {"difficulty": "expert"}),
        ((0, 0), {"typo_axis": 1}),
    ),
)
def test_invalid_request_envelope_fails_loudly(args, kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(*args, **kwargs)


def test_every_schedule_rotation_refutes_every_declared_competitor():
    for band in BANDS:
        for start in range(GEN.LESSON_SCHEDULE_PERIOD):
            grids = [GEN.generate(404, start + offset, difficulty=band) for offset in range(5)]
            for query_index in range(5):
                demos = [grid for index, grid in enumerate(grids) if index != query_index]
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(rival(grid) != GEN._intended_output(grid) for grid in demos), (
                        band,
                        start,
                        query_index,
                        name,
                    )


def test_retained_audit_witness_refutes_first_nonrectangular():
    grid = [
        [2, 2, 0, 1, 0],
        [2, 0, 0, 1, 0],
        [0, 0, 1, 1, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]
    assert GEN._intended_output(grid) == [[0, 1], [0, 1], [1, 1]]
    assert GEN._rival_first_nonrectangular(grid) == [[2, 2], [2, 0]]


def test_multicolor_connected_witness_refutes_color_split_shortcut():
    grid = GEN.generate(1234, 2, difficulty="medium", target_shape="cross")
    assert GEN.SEMANTIC_WITNESSES["mixed_color_winner"](grid)
    assert GEN._rival_same_color_components(grid) != GEN._intended_output(grid)
