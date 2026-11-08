"""Task-local semantic regressions for cf09cffb4663.

These tests are source/runtime portable and intentionally exercise the public
contract rather than implementation details.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
for parent in HOME.parents:
    if (parent / "shared/runtime/puzzle_generators/base.py").is_file():
        ROOT = parent
        sys.path.insert(0, str(ROOT / "shared/runtime"))
        CANONICAL = ROOT / "shared/data/canonical/puzzles.jsonl"
        break
    if (parent / "puzzle_generators/base.py").is_file():
        ROOT = parent
        sys.path.insert(0, str(ROOT))
        CANONICAL = ROOT / "data/canonical/puzzles.jsonl"
        break
else:  # pragma: no cover - packaging/runtime contract
    raise RuntimeError("No independent puzzle_generators runtime found")

spec = importlib.util.spec_from_file_location("reviewed_cf09cffb4663", HOME / "generator.py")
gen = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gen)

CANONICAL_SHAPES = {(8, 10), (9, 9), (9, 11), (10, 10)}
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def canonical_pairs():
    with CANONICAL.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return list(row["train"]) + list(row["test"])
    raise AssertionError("canonical task missing")


def target_centers(grid):
    h, w = len(grid), len(grid[0])
    return {
        (r, c)
        for r in range(1, h - 1)
        for c in range(1, w - 1)
        if grid[r][c] == 1
        and all(grid[r + dr][c + dc] == 1 for dr, dc in CARDINAL)
    }


def components(grid):
    unseen = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1}
    out = []
    while unseen:
        stack = [unseen.pop()]
        component = set(stack)
        while stack:
            r, c = stack.pop()
            for dr, dc in CARDINAL:
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    stack.append(point)
        out.append(component)
    return out


def component_for(point, groups):
    return next(group for group in groups if point in group)


def degree(grid, point):
    r, c = point
    h, w = len(grid), len(grid[0])
    return sum(
        0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] == 1
        for dr, dc in CARDINAL
    )


def demos(seed, start, band):
    result = []
    for index in range(start, start + gen.EXAMPLES_NEEDED):
        grid = gen.generate(seed, index, difficulty=band)
        result.append({"input": grid, "output": gen.rule_mirror(grid)})
    return result


def test_authority_pin_and_small_exact_axis_surface():
    assert gen.RULE_HASH == "4584c31c95ef"
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_crosses"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    for key in (
        "typo_axis",
        "palette_kind",
        "palette_size",
        "position_bias",
        "n_distinct_colors",
        "density",
        "texture",
    ):
        with pytest.raises((TypeError, ValueError), match=key):
            gen.generate(0, 0, **{key: 1})


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 0]],
        [[True, 0], [0, 1]],
        [[10, 0], [0, 0]],
        [[-1, 0], [0, 0]],
        [[1.0, 0], [0, 0]],
        [[9]],
        [[0] * 9 for _ in range(9)],
        [[1] * 9 for _ in range(9)],
        [[0, 1, 0], [1, 1, 1], [0, 1, 0]],
    ],
)
def test_bad_grids_rejected_without_crashing(grid):
    assert gen.self_check(grid)


def test_canonical_pairs_are_owned_and_mirrored_exactly():
    for pair in canonical_pairs():
        assert not gen.self_check(pair["input"])
        assert not gen.strict_canonical_like(pair["input"])
        original = copy.deepcopy(pair["input"])
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height", [8, 9, 10])
@pytest.mark.parametrize("width", [9, 10, 11])
@pytest.mark.parametrize("count", [1, 2])
def test_every_advertised_exact_override_is_realized(band, height, width, count):
    grid = gen.generate(
        29,
        17,
        difficulty=band,
        grid_h=height,
        grid_w=width,
        n_crosses=count,
    )
    assert (len(grid), len(grid[0])) == (height, width)
    assert len(target_centers(grid)) == count
    assert gen.observe_overrides(grid) == {
        "grid_h": height,
        "grid_w": width,
        "n_crosses": count,
    }
    assert not gen.self_check(grid)


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 7},
        {"grid_h": 11},
        {"grid_w": 8},
        {"grid_w": 12},
        {"n_crosses": 0},
        {"n_crosses": 3},
        {"grid_h": True},
        {"grid_w": 9.0},
        {"n_crosses": "1"},
    ],
)
def test_invalid_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


def test_default_curriculum_is_deterministic_diverse_and_canonical_scaled():
    unique = set()
    target_sizes = set()
    saw_t_junction = False
    for band in ("easy", "medium", "hard"):
        for seed in range(30):
            sample_index = seed * 7 + 2
            grid = gen.generate(seed, sample_index, difficulty=band)
            assert grid == gen.generate(seed, sample_index, difficulty=band)
            assert (len(grid), len(grid[0])) in CANONICAL_SHAPES
            assert not gen.self_check(grid)
            assert gen.rule_mirror(grid) != grid
            unique.add(json.dumps(grid, separators=(",", ":")))
            groups = components(grid)
            for center in target_centers(grid):
                target_sizes.add(len(component_for(center, groups)))
            saw_t_junction |= any(
                degree(grid, point) == 3
                for group in groups
                if not (group & target_centers(grid))
                for point in group
            )
    assert min(target_sizes) < 9
    assert max(target_sizes) >= 9
    assert 5 not in target_sizes
    assert saw_t_junction
    assert len(unique) >= 80


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(9))
def test_every_cyclic_three_demo_window_refutes_declared_competitors(band, start):
    lesson = demos(seed=701 + start, start=start, band=band)
    query_grid = gen.generate(701 + start, start + gen.EXAMPLES_NEEDED, difficulty=band)
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
    assert gen.lesson_identifiable(lesson, query) == []
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in lesson), name


def test_declared_canonical_shortcuts_really_fit_all_canonical_pairs():
    pairs = canonical_pairs()
    assert gen.CANONICAL_SHORTCUTS
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name


def test_prior_exact_five_component_shortcut_is_now_refuted():
    for band in ("easy", "medium", "hard"):
        for index in range(12):
            grid = gen.generate(811, index, difficulty=band)
            intended = gen.rule_mirror(grid)
            assert gen.rival_exact_five_component(grid) != intended
            groups = components(grid)
            assert all(len(component_for(center, groups)) != 5 for center in target_centers(grid))


def test_mutation_fixtures_are_all_rejected():
    fixtures = gen.mutation_fixtures()
    assert fixtures
    for name, grid in fixtures:
        assert gen.self_check(grid), name
