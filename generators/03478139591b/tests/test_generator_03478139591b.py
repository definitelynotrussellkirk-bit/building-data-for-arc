from __future__ import annotations

import importlib.util
import random
from pathlib import Path

import pytest


TASK = "03478139591b"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"generator_{TASK}", HOME / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GEN)


def test_rule_binding_and_canonical_mirror_are_pinned():
    assert GEN.RULE_HASH == "e5a2cb4531f0"
    grid = [[5, 5, 5], [0, 0, 5], [0, 0, 0]]
    assert GEN.rule_mirror(grid) == [[0, 0, 0], [4, 4, 0], [4, 4, 4]]


def test_self_check_rejects_known_invalid_endpoints_and_malformed_cells():
    invalid = {
        "all_zero": [[0, 0], [0, 0]],
        "all_foreground": [[3, 3], [3, 3]],
        "boolean": [[0, True], [0, 0]],
        "ragged": [[0, 3], [0]],
        "mixed_foregrounds": [[0, 3], [5, 0]],
        "out_of_range": [[0, 10], [0, 0]],
    }
    for name, grid in invalid.items():
        errors = GEN.self_check(grid)
        assert errors, name
        assert all(isinstance(error, str) for error in errors)


def test_unknown_and_coercive_overrides_are_rejected_loudly():
    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(0, 0, typo_axis=1)
    with pytest.raises(TypeError, match="fg_color"):
        GEN.generate(0, 0, fg_color=True)
    with pytest.raises(TypeError, match="fg_density"):
        GEN.generate(0, 0, fg_density="0.5")
    with pytest.raises(ValueError, match="texture"):
        GEN.generate(0, 0, texture="all_fg")


def test_declared_size_and_color_boundaries_are_realizable_exactly():
    for height, width, color, layout in (
        (3, 15, 3, "row"),
        (15, 3, 5, "column"),
        (15, 15, 8, "border"),
        (4, 7, 9, "diagonal"),
    ):
        grid = GEN.generate(
            91,
            height * 100 + width,
            grid_h=height,
            grid_w=width,
            fg_color=color,
            fg_density=0.45,
            fg_layout=layout,
        )
        assert (len(grid), len(grid[0])) == (height, width)
        assert set(cell for row in grid for cell in row) == {0, color}
        assert GEN.self_check(grid) == []


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_ordinary_generation_always_has_visible_binary_complement(difficulty):
    for seed in range(24):
        grid = GEN.generate(seed=seed, sample_index=seed * 17 + 3, difficulty=difficulty)
        colors = {cell for row in grid for cell in row}
        assert 0 in colors and len(colors) == 2
        assert GEN.self_check(grid, difficulty=difficulty) == []
        output = GEN.rule_mirror(grid)
        assert output != grid
        assert all(type(cell) is int and 0 <= cell <= 9 for row in output for cell in row)


def test_generation_is_deterministic_fresh_and_global_rng_independent():
    random.seed(7123)
    before = random.getstate()
    first = GEN.generate(404, 17, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(404, 17, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert GEN.generate(404, 17, difficulty="hard") == second
