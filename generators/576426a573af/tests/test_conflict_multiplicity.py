"""Regressions for the retained conflict-count shortcut and scalar defects."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
for parent in (HOME, *HOME.parents):
    # Portable snapshots also carry shared/runtime mirrors. Execution-layout
    # dependencies must win so the selected-source loader sees one source tree.
    if (parent / "puzzle_generators/base.py").is_file():
        sys.path.insert(0, str(parent))
        break
    if (parent / "shared/runtime/puzzle_generators/base.py").is_file():
        sys.path.insert(0, str(parent / "shared/runtime"))
        break
else:  # pragma: no cover - packaging contract
    raise RuntimeError("No independent puzzle_generators runtime found")

from reviewer_support import canonical_pairs, find_root  # noqa: E402

spec = importlib.util.spec_from_file_location("multiplicity_576426a573af", HOME / "generator.py")
gen = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gen)


def conflicts(grid):
    h = len(grid)
    return [
        (r, h - 1 - r, c)
        for r in range(h // 2)
        for c in range(len(grid[0]))
        if grid[r][c] and grid[h - 1 - r][c]
        and grid[r][c] != grid[h - 1 - r][c]
    ]


def official(grid):
    h = len(grid)
    return [[value or grid[h - 1 - r][c] for c, value in enumerate(row)]
            for r, row in enumerate(grid)]


def count_limited_rival(grid):
    out = official(grid)
    for top, bottom, col in conflicts(grid)[1:]:
        out[top][col], out[bottom][col] = grid[bottom][col], grid[top][col]
    return out


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("index", [1, 3])
@pytest.mark.parametrize("palette_size", [3, 4, 5, 6])
def test_conflict_roles_reject_the_count_limited_rival_at_minimum_capacity(band, index, palette_size):
    """A return to one conflict, or palette loss while adding pairs, must fail."""
    for seed in (0, 17, 991):
        grid = gen.generate(seed, index, difficulty=band,
                            grid_h=4, grid_w=3, fg_palette_size=palette_size)
        assert len(conflicts(grid)) >= 2
        assert count_limited_rival(grid) != official(grid)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == {
            "grid_h": 4, "grid_w": 3, "fg_palette_size": palette_size,
        }


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_count_limited_rival_is_taught_for_all_starts_rotations_and_four_queries(band):
    """Removing either repeated multiplicity witness must break a rotation."""
    for start in range(8):
        grids = [gen.generate(3100 + start, index, difficulty=band)
                 for index in range(start, start + 8)]
        pairs = [{"input": grid, "output": official(grid)} for grid in grids]
        demos = pairs[:4]
        assert any(count_limited_rival(pair["input"]) != pair["output"] for pair in demos)
        assert len({tuple(map(tuple, grid)) for grid in grids}) == 8
        for query in pairs[4:]:
            assert gen.lesson_identifiable(demos, query) == []
        for holdout in range(5):
            rotated = [pair for index, pair in enumerate(pairs[:5]) if index != holdout]
            assert any(count_limited_rival(pair["input"]) != pair["output"] for pair in rotated)
            assert gen.lesson_identifiable(rotated, pairs[holdout]) == []


def test_declared_count_limited_rival_matches_the_canonical_pairs_and_literal_counterexample():
    grid = [[1, 3, 0], [0, 0, 5], [0, 0, 0], [2, 4, 0]]
    expected = [[1, 3, 0], [0, 0, 5], [0, 0, 5], [2, 4, 0]]
    rival_expected = [[1, 4, 0], [0, 0, 5], [0, 0, 5], [2, 3, 0]]
    original = copy.deepcopy(grid)
    assert official(grid) == expected
    assert count_limited_rival(grid) == rival_expected
    assert gen.self_check(grid) == []
    assert "preserve_first_conflict_only" in gen.LESSON_COMPETITORS
    rival = gen.LESSON_COMPETITORS["preserve_first_conflict_only"]
    assert rival(grid) == rival_expected
    assert grid == original
    assert all(rival(pair["input"]) == pair["output"]
               for pair in canonical_pairs(gen.TASK_ID, root=find_root(__file__)))
    witnesses = [name for name, names in gen.WITNESS_RIVALS.items()
                 if "preserve_first_conflict_only" in names]
    assert witnesses
    assert all(gen.SEMANTIC_WITNESSES[name](grid) for name in witnesses)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("argument,value", [
    ("seed", True), ("seed", False), ("seed", 1.0), ("seed", 1.75), ("seed", "1"),
    ("sample_index", True), ("sample_index", False), ("sample_index", 1.0),
    ("sample_index", 1.75), ("sample_index", "1"), ("sample_index", -1),
])
def test_request_scalars_are_rejected_before_coercion(band, argument, value):
    kwargs = {"seed": 991, "sample_index": 0, "difficulty": band, argument: value}
    with pytest.raises((TypeError, ValueError), match=argument):
        gen.generate(**kwargs)


def test_negative_integer_seed_remains_a_legal_deterministic_family():
    first = gen.generate(-17, 3, difficulty="hard")
    assert gen.self_check(first) == []
    assert first == gen.generate(-17, 3, difficulty="hard")
