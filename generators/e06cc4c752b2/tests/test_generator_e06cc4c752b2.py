from __future__ import annotations

import importlib.util
import random
from pathlib import Path

import pytest


TASK = "e06cc4c752b2"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"generator_{TASK}", HOME / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GEN)


def _markers(grid):
    return [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value]


def test_rule_binding_and_canonical_mirror_are_pinned():
    assert GEN.RULE_HASH == "4cf331b98beb"
    grid = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 2, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 5, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]
    assert GEN.rule_mirror(grid) == [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 2, 2, 2, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 5, 5, 5, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]


def test_self_check_rejects_malformed_or_rule_ambiguous_inputs():
    invalid = {
        "empty": [],
        "too_small": [[0, 0, 0], [0, 2, 0]],
        "ragged": [[0, 0, 0, 0, 0], [0, 2, 0, 0]],
        "boolean": [[0, 0, 0, 0, 0], [0, True, 0, 0, 0], [0, 0, 0, 0, 0]],
        "no_markers": [[0] * 5 for _ in range(3)],
        "horizontal_edge": [[2, 0, 0, 0, 0], [0] * 5, [0] * 5],
        "cardinal_neighbors": [[0] * 5, [0, 2, 2, 0, 0], [0] * 5],
        "diagonal_neighbors": [[0, 2, 0, 0, 0], [0, 0, 3, 0, 0], [0] * 5],
        "touching_expansions": [[0] * 9, [0, 2, 0, 0, 3, 0, 0, 0, 0], [0] * 9],
        "out_of_range": [[0] * 5, [0, 10, 0, 0, 0], [0] * 5],
    }
    for name, grid in invalid.items():
        errors = GEN.self_check(grid)
        assert errors, name
        assert all(type(error) is str for error in errors)


def test_unknown_coercive_and_impossible_overrides_are_rejected_loudly():
    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(0, 0, typo_axis=1)
    with pytest.raises(TypeError, match="grid_h"):
        GEN.generate(0, 0, grid_h=True)
    with pytest.raises(TypeError, match="n_markers"):
        GEN.generate(0, 0, n_markers="2")
    with pytest.raises(ValueError, match="palette_kind"):
        GEN.generate(0, 0, palette_kind="invented")
    with pytest.raises(ValueError, match="capacity"):
        GEN.generate(0, 0, grid_h=3, grid_w=5, n_markers=8)


def test_declared_boundaries_and_exact_marker_count_are_realizable():
    cases = (
        (3, 5, 1, "monochrome"),
        (5, 16, 4, "warm"),
        (15, 5, 6, "cool"),
        (15, 16, 8, "varied"),
    )
    for height, width, count, palette in cases:
        grid = GEN.generate(
            91,
            height * 100 + width + count,
            grid_h=height,
            grid_w=width,
            n_markers=count,
            palette_kind=palette,
        )
        assert (len(grid), len(grid[0])) == (height, width)
        assert len(_markers(grid)) == count
        assert GEN.self_check(grid) == []
        if palette == "monochrome":
            assert len({value for _, _, value in _markers(grid)}) == 1


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_ordinary_generation_is_valid_and_every_marker_becomes_one_three_bar(difficulty):
    for seed in range(32):
        grid = GEN.generate(seed, seed * 31 + 7, difficulty=difficulty)
        markers = _markers(grid)
        assert 1 <= len(markers) <= 8
        assert GEN.self_check(grid, difficulty=difficulty) == []
        output = GEN.rule_mirror(grid)
        assert output != grid
        assert sum(value != 0 for row in output for value in row) == 3 * len(markers)
        for r, c, value in markers:
            assert output[r][c - 1:c + 2] == [value, value, value]


def test_generation_is_deterministic_fresh_and_global_rng_independent():
    random.seed(8192)
    before = random.getstate()
    first = GEN.generate(404, 17, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(404, 17, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert GEN.generate(404, 17, difficulty="hard") == second
