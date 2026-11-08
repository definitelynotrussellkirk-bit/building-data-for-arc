from __future__ import annotations

import importlib.util
import random
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK = "85305305afdf"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"generator_{TASK}", HOME / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GEN)


def _counts(grid):
    values = [cell for row in grid for cell in row if cell != 0]
    movable = sum(
        1
        for r, row in enumerate(grid)
        for c, cell in enumerate(row[:-1])
        if cell != 0 and row[c + 1] == 0
    )
    blocked = sum(
        1
        for row in grid
        for c, cell in enumerate(row[:-1])
        if cell != 0 and row[c + 1] != 0
    )
    return values, movable, blocked


def test_rule_binding_and_all_canonical_pairs_are_exact():
    assert GEN.RULE_HASH == "dfecf6d0b7a6"
    pairs = canonical_pairs(TASK, root=find_root(__file__))
    assert len(pairs) == 3
    for pair in pairs:
        source = pair["input"]
        before = [row[:] for row in source]
        assert GEN.self_check(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == before


def test_rule_mirror_moves_only_the_terminal_cell_of_each_horizontal_run():
    grid = [
        [1, 2, 3, 0, 0, 4, 0],
        [0, 5, 6, 0, 7, 8, 0],
    ]
    assert GEN.rule_mirror(grid) == [
        [1, 2, 0, 3, 0, 0, 4],
        [0, 5, 0, 6, 7, 0, 8],
    ]


def test_self_check_rejects_malformed_and_unteaching_domains():
    invalid = {
        "empty": [],
        "ragged": [[0, 1], [0]],
        "boolean": [[0, True, 0], [0, 0, 0]],
        "out_of_range": [[0, 10, 0], [0, 0, 0]],
        "all_zero": [[0, 0, 0], [0, 0, 0]],
        "right_edge_only": [[0, 0, 3], [0, 0, 0]],
        "all_movable": [[2, 0, 0, 3, 0], [0, 0, 0, 0, 0]],
        "all_blocked": [[2, 3, 4, 5], [0, 0, 0, 0]],
    }
    for name, grid in invalid.items():
        assert GEN.self_check(grid), name


def test_unknown_coercive_and_contradictory_overrides_fail_loudly():
    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(1, 2, typo_axis=1)
    with pytest.raises(TypeError, match="grid_h"):
        GEN.generate(1, 2, grid_h=True)
    with pytest.raises(TypeError, match="n_distinct_colors"):
        GEN.generate(1, 2, n_distinct_colors="3")
    with pytest.raises(ValueError, match="n_distinct_colors"):
        GEN.generate(1, 2, cells=3, n_distinct_colors=4)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 2, difficulty="extreme")


def test_declared_boundaries_are_realized_exactly():
    for h, w, cells, colors in ((3, 4, 3, 1), (12, 16, 12, 9), (7, 9, 8, 4)):
        grid = GEN.generate(
            101 + h,
            203 + w,
            grid_h=h,
            grid_w=w,
            cells=cells,
            n_distinct_colors=colors,
        )
        values, movable, blocked = _counts(grid)
        assert (len(grid), len(grid[0])) == (h, w)
        assert len(values) == cells
        assert len(set(values)) == colors
        assert movable >= 1 and blocked >= 1
        assert GEN.self_check(grid) == []


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_ordinary_generation_teaches_moving_and_stationary_branches(difficulty):
    seen = set()
    for seed in range(40):
        grid = GEN.generate(seed, seed * 29 + 7, difficulty=difficulty)
        values, movable, blocked = _counts(grid)
        assert values and movable >= 1 and blocked >= 1
        assert GEN.self_check(grid, difficulty=difficulty) == []
        output = GEN.rule_mirror(grid)
        assert output != grid
        assert sorted(cell for row in output for cell in row if cell) == sorted(values)
        seen.add(tuple(tuple(row) for row in grid))
    assert len(seen) == 40


def test_generation_is_deterministic_fresh_and_global_rng_independent():
    kwargs = dict(difficulty="hard", grid_h=12, grid_w=16, cells=12, n_distinct_colors=7)
    random.seed(8675309)
    before = random.getstate()
    first = GEN.generate(701, 809, **kwargs)
    assert random.getstate() == before
    expected = [row[:] for row in first]
    first[0][0] = 9 if first[0][0] != 9 else 8
    second = GEN.generate(701, 809, **kwargs)
    assert second == expected
    assert first is not second and first[0] is not second[0]
