from __future__ import annotations

import importlib.util
import random
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK = "1ec277b81469"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"generator_{TASK}", HOME / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GEN)


def _stats(grid):
    active = [row for row in grid if any(cell != 0 for cell in row)]
    values = [cell for row in grid for cell in row if cell != 0]
    return len(active), len(values), len(set(values))


def test_rule_binding_and_all_canonical_pairs_are_exact():
    assert GEN.RULE_HASH == "6ab6552b1d13"
    pairs = canonical_pairs(TASK, root=find_root(__file__))
    assert len(pairs) == 4
    for pair in pairs:
        source = pair["input"]
        before = [row[:] for row in source]
        assert GEN.self_check(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == before


def test_rule_mirror_right_packs_each_row_and_preserves_order():
    grid = [
        [0, 2, 0, 3, 0, 0, 4],
        [5, 0, 0, 6, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [7, 0, 8, 0, 9, 0, 1],
    ]
    assert GEN.rule_mirror(grid) == [
        [0, 0, 0, 0, 2, 3, 4],
        [0, 0, 0, 0, 0, 5, 6],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 7, 8, 9, 1],
    ]


def test_self_check_rejects_malformed_and_unteaching_domains():
    invalid = {
        "empty": [],
        "ragged": [[0, 1], [0]],
        "boolean": [[0, True, 0], [0, 0, 0]],
        "out_of_range": [[0, 10, 0], [0, 0, 0]],
        "all_zero": [[0, 0, 0], [0, 0, 0]],
        "one_active_row": [[2, 0, 3, 0], [0, 0, 0, 0]],
        "no_order_example": [[2, 0, 0], [0, 3, 0]],
        "already_right_packed": [[0, 0, 2, 3], [0, 0, 0, 4]],
    }
    for name, grid in invalid.items():
        assert GEN.self_check(grid), name


def test_unknown_coercive_and_contradictory_overrides_fail_loudly():
    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(1, 2, texture="no_active_rows")
    with pytest.raises(TypeError, match="grid_h"):
        GEN.generate(1, 2, grid_h=True)
    with pytest.raises(TypeError, match="n_distinct_colors"):
        GEN.generate(1, 2, n_distinct_colors="3")
    with pytest.raises(ValueError, match="active_rows"):
        GEN.generate(1, 2, grid_h=4, active_rows=5)
    with pytest.raises(ValueError, match="cells"):
        GEN.generate(1, 2, grid_h=4, grid_w=5, active_rows=4, cells=4)
    with pytest.raises(ValueError, match="n_distinct_colors"):
        GEN.generate(1, 2, active_rows=2, cells=3, n_distinct_colors=4)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 2, difficulty="extreme")


def test_declared_boundaries_are_realized_exactly():
    cases = (
        (4, 5, 2, 3, 1),
        (14, 18, 14, 238, 9),
        (8, 12, 5, 37, 7),
    )
    for height, width, active_rows, cells, colors in cases:
        grid = GEN.generate(
            101 + height,
            203 + width,
            grid_h=height,
            grid_w=width,
            active_rows=active_rows,
            cells=cells,
            n_distinct_colors=colors,
        )
        assert (len(grid), len(grid[0])) == (height, width)
        assert _stats(grid) == (active_rows, cells, colors)
        assert GEN.self_check(grid) == []
        assert GEN.rule_mirror(grid) != grid


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_ordinary_generation_is_valid_varied_and_nontrivial(difficulty):
    seen = set()
    shapes = set()
    for seed in range(40):
        grid = GEN.generate(seed, seed * 29 + 7, difficulty=difficulty)
        assert GEN.self_check(grid, difficulty=difficulty) == []
        output = GEN.rule_mirror(grid)
        assert output != grid
        assert sorted(cell for row in output for cell in row if cell) == sorted(
            cell for row in grid for cell in row if cell
        )
        seen.add(tuple(tuple(row) for row in grid))
        shapes.add((len(grid), len(grid[0])))
    assert len(seen) == 40
    assert len(shapes) >= 3


def test_generation_is_deterministic_fresh_and_global_rng_independent():
    kwargs = dict(
        difficulty="hard",
        grid_h=14,
        grid_w=18,
        active_rows=11,
        cells=129,
        n_distinct_colors=8,
    )
    random.seed(8675309)
    before = random.getstate()
    first = GEN.generate(701, 809, **kwargs)
    assert random.getstate() == before
    expected = [row[:] for row in first]
    first[0][0] = 9 if first[0][0] != 9 else 8
    second = GEN.generate(701, 809, **kwargs)
    assert second == expected
    assert first is not second and first[0] is not second[0]
