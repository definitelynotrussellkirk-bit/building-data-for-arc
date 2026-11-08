from __future__ import annotations

import importlib.util
import random

import pytest

from reviewer_support import find_root


TASK_ID = "1ee7274bdbb0"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"axis_repairs_{TASK_ID}", SOURCE)
assert SPEC is not None and SPEC.loader is not None
generator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generator)

# These are per-input invariants; periodic curriculum witnesses need not all
# fire on a single grid or on an explicitly overridden marker-count population.
PER_INPUT_WITNESSES = (
    "marked_rotation_visible", "unmarked_copy_control", "mixed_marker_control",
    "motif_size_distractor", "marker_not_answer",
)


def _clockwise(cells, size):
    return {(col, size - 1 - row) for row, col in cells}


def _assert_marker_contract(motif, markers, size, count, forbidden=()):
    answer = _clockwise(motif, size)
    assert len(markers) == count
    assert not (markers & motif)
    assert not (markers & set(forbidden))
    assert markers - answer
    assert answer - markers


@pytest.mark.parametrize(
    "seed,index,overrides",
    [
        (0, 41096, {}),
        (
            0,
            1543,
            {
                "tile_size": 5,
                "n_tile_rows": 1,
                "n_tile_cols": 2,
                "shape_size": 6,
                "rotate_flag": False,
                "n_flag_cells": 1,
            },
        ),
    ],
)
def test_connected_sampler_regression_seeds(seed, index, overrides):
    grid = generator.generate(seed, index, difficulty="hard", **overrides)
    assert generator.self_check(grid, meta={"overrides": overrides}) == []
    assert all(generator.SEMANTIC_WITNESSES[name](grid) for name in PER_INPUT_WITNESSES)
    assert generator.generate(seed, index, difficulty="hard", **overrides) == grid


def test_singleton_multiple_marker_witness_regression():
    controls = {
        "tile_size": 3,
        "n_tile_rows": 1,
        "n_tile_cols": 2,
        "shape_size": 1,
        "rotate_flag": True,
        "n_flag_cells": 2,
    }
    grid = generator.generate(127, 1, difficulty="easy", **controls)
    assert generator.observe_overrides(grid) == controls
    assert generator.self_check(grid, meta={"overrides": controls}) == []
    assert generator.SEMANTIC_WITNESSES["marker_not_answer"](grid)


class _FirstChoiceRandom(random.Random):
    """Keep proposing a corner singleton to exercise the finite fallback."""

    def choice(self, values):
        return values[0]

    def sample(self, population, count):
        return list(population)[:count]


@pytest.mark.parametrize("size", [3, 4, 5])
def test_sampler_has_finite_fallback_for_rejected_proposals(size):
    motif = generator._sample_mask(_FirstChoiceRandom(13), size, 1, connected=True)
    assert len(motif) == 1
    clockwise = _clockwise(motif, size)
    assert clockwise != motif
    assert clockwise != {(row, size - 1 - col) for row, col in motif}
    assert clockwise != {(size - 1 - row, col) for row, col in motif}


@pytest.mark.parametrize("size", [3, 4, 5])
def test_nondistinguishing_mode_allows_rotating_corner_motifs(size):
    motif = generator._sample_mask(
        _FirstChoiceRandom(13), size, 1, connected=None, distinguishing=False
    )
    assert motif == {(0, 0)}
    assert _clockwise(motif, size) != motif


@pytest.mark.parametrize("size", [3, 4, 5])
@pytest.mark.parametrize("count", [1, 2, 3])
def test_marker_placement_leaves_answer_and_marker_witness_cells(size, count):
    motif = {(0, 1)}
    for seed in range(32):
        markers = generator._place_markers(random.Random(seed), motif, size, count)
        _assert_marker_contract(motif, markers, size, count)


def test_dense_motif_allows_markers_in_every_empty_cell():
    motif = {(row, col) for row in range(2) for col in range(3)}
    markers = generator._place_markers(random.Random(7), motif, 3, 3)
    _assert_marker_contract(motif, markers, 3, 3)
    assert markers == {(2, 0), (2, 1), (2, 2)}


def test_forbidden_answer_cell_already_protects_the_marker_witness():
    motif = {(0, 1)}
    forbidden = frozenset({(1, 1), (1, 2)})
    markers = generator._place_markers(
        random.Random(7), motif, 3, 3, forbidden=forbidden
    )
    _assert_marker_contract(motif, markers, 3, 3, forbidden)


def test_impossible_forbidden_marker_layout_raises_instead_of_reducing_count():
    motif = {(0, 1)}
    allowed = {(1, 2), (2, 2)}
    forbidden = frozenset(
        {(row, col) for row in range(3) for col in range(3)} - motif - allowed
    )
    with pytest.raises(ValueError, match="uncovered|answer"):
        generator._place_markers(random.Random(7), motif, 3, 2, forbidden=forbidden)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("tile_size", [3, 4, 5])
@pytest.mark.parametrize("shape_size", [1, 6])
@pytest.mark.parametrize("marker_count", [1, 2, 3])
@pytest.mark.parametrize("anchor_marked", [False, True])
def test_exact_boundary_controls_keep_all_semantic_witnesses(
    difficulty, tile_size, shape_size, marker_count, anchor_marked
):
    controls = {
        "tile_size": tile_size,
        "n_tile_rows": 1,
        "n_tile_cols": 2,
        "shape_size": shape_size,
        "rotate_flag": anchor_marked,
        "n_flag_cells": marker_count,
    }
    first = generator.generate(127, 1, difficulty=difficulty, **controls)
    assert generator.observe_overrides(first) == controls
    assert generator.self_check(first, meta={"overrides": controls}) == []
    assert all(generator.SEMANTIC_WITNESSES[name](first) for name in PER_INPUT_WITNESSES)
    second = generator.generate(127, 1, difficulty=difficulty, **controls)
    assert second == first
    assert second is not first
    assert all(first_row is not second_row for first_row, second_row in zip(first, second))
