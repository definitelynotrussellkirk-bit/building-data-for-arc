"""Regression tests for the unique left-right-asymmetric crop generator."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "1a5d49e539de"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _components8(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = rr + dr, cc + dc
                        if (
                            0 <= nr < height
                            and 0 <= nc < width
                            and (nr, nc) not in seen
                            and grid[nr][nc] == color
                        ):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            components.append((color, cells))
    return components




def _components4(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append((color, cells))
    return components

def _normalized(cells):
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return {(row - row0, col - col0) for row, col in cells}


def _is_lr_symmetric(cells):
    normalized = _normalized(cells)
    width = max(col for _, col in normalized) + 1
    return all((row, width - 1 - col) in normalized for row, col in normalized)


def _crop_component(grid, component):
    _, cells = component
    row0 = min(row for row, _ in cells)
    row1 = max(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    col1 = max(col for _, col in cells)
    return [row[col0:col1 + 1] for row in grid[row0:row1 + 1]]


def _oracle(grid):
    asymmetric = [component for component in _components8(grid)
                  if not _is_lr_symmetric(component[1])]
    assert len(asymmetric) == 1
    return _crop_component(grid, asymmetric[0])


def _canonical():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
    unique = []
    seen = set()
    for pair in pairs:
        key = (repr(pair["input"]), repr(pair["output"]))
        if key not in seen:
            seen.add(key)
            unique.append(pair)
    return unique


def test_rule_hash_and_all_canonical_pairs_are_pinned_and_solved():
    assert GEN.RULE_HASH == "71d6cfb99295"
    pairs = _canonical()
    assert len(pairs) == 4
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert 8 <= len(_components4(source)) <= 13
        assert GEN.rule_mirror(source) == pair["output"]
        assert _oracle(source) == pair["output"]
        assert source == pair["input"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("grid_size,color", [(20, 1), (23, 9)])
def test_exact_overrides_are_observable_in_every_band(band, grid_size, color):
    grid = GEN.generate(1701, 7, difficulty=band, grid_size=grid_size, color=color)
    assert len(grid) == grid_size
    assert {len(row) for row in grid} == {grid_size}
    assert {cell for row in grid for cell in row if cell} == {color}
    assert GEN.observe_overrides(grid) == {"grid_size": grid_size, "color": color}
    assert GEN.self_check(grid) == []
    assert GEN.rule_mirror(grid) == _oracle(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"bogus_axis": 1},
        {"grid_size": 19},
        {"grid_size": 24},
        {"grid_size": True},
        {"color": 0},
        {"color": 10},
        {"color": 2.5},
    ],
)
def test_invalid_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, **kwargs)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="impossible")


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_matches_the_task_domain_and_is_diverse(band):
    outputs = set()
    max_object_size = 0
    target_indices = set()
    target_ranks = set()
    for index in range(72):
        grid = GEN.generate(9000 + index, index, difficulty=band)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert grid == GEN.generate(9000 + index, index, difficulty=band)
        assert 20 <= len(grid) <= 23 and len(grid) == len(grid[0])
        assert len({cell for row in grid for cell in row if cell}) == 1

        components = _components8(grid)
        assert len(components) == 4
        assert len(_components4(grid)) == 10
        asymmetric = [i for i, component in enumerate(components)
                      if not _is_lr_symmetric(component[1])]
        assert len(asymmetric) == 1
        target_index = asymmetric[0]
        sizes = [len(component[1]) for component in components]
        target_size = sizes[target_index]
        max_object_size = max(max_object_size, *sizes)
        target_indices.add(target_index)
        target_ranks.add(sum(size < target_size for size in sizes))
        output = GEN.rule_mirror(grid)
        assert output == _oracle(grid)
        outputs.add(tuple(tuple(row) for row in output))

    assert max_object_size >= 20
    assert len(outputs) >= 45
    assert target_indices == {0, 1, 2, 3}
    assert {0, 1, 3} <= target_ranks


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_consecutive_three_demo_lesson_refutes_declared_rivals(band):
    for start in range(16):
        pairs = []
        for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
            grid = GEN.generate(12000 + start, sample_index, difficulty=band)
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        demos, query = pairs[:-1], pairs[-1]
        assert GEN.lesson_identifiable(demos, query) == []
        assert set(GEN.schedule_profile(12000 + start, i, band)
                   for i in range(start, start + 3)) == set(GEN.SCHEDULE_PROFILES)
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert any(rival(demo["input"]) != demo["output"] for demo in demos), name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_query_rotation_uses_actual_rival_refutation_not_profile_checklists(band):
    for start in range(8):
        pairs = []
        for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
            grid = GEN.generate(13000 + start, sample_index, difficulty=band)
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(demo["input"]) != demo["output"] for demo in demos), name


def test_each_canonical_shortcut_is_refuted_by_at_least_one_official_pair():
    pairs = _canonical()
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in pairs), name


def test_self_check_rejects_trivial_and_structural_impostors():
    valid = GEN.generate(444, 5, grid_size=20, color=6)
    assert GEN.self_check(valid) == []

    all_background = [[0] * 20 for _ in range(20)]
    full_color = [[6] * 20 for _ in range(20)]
    singleton = [[0] * 20 for _ in range(20)]
    singleton[10][10] = 6
    short_line = [[0] * 20 for _ in range(20)]
    short_line[10][8:11] = [6, 6, 6]

    only_three = copy.deepcopy(valid)
    _, removed = _components8(valid)[0]
    for row, col in removed:
        only_three[row][col] = 0

    multicolor = copy.deepcopy(valid)
    _, recolored = _components8(valid)[0]
    for row, col in recolored:
        multicolor[row][col] = 7

    for name, grid in {
        "all_background": all_background,
        "full_color": full_color,
        "singleton": singleton,
        "short_line": short_line,
        "only_three": only_three,
        "multicolor": multicolor,
    }.items():
        assert GEN.self_check(grid), name


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 20 for _ in range(20)]])
def test_malformed_inputs_return_diagnostics_instead_of_raising(grid):
    assert GEN.self_check(grid)
    assert GEN.strict_canonical_like(grid)


def test_generation_is_fresh_deterministic_and_global_rng_pure():
    random.seed(987654321)
    before = random.getstate()
    first = GEN.generate(8080, 17, difficulty="hard")
    intervening = GEN.generate(8081, 18, difficulty="easy")
    second = GEN.generate(8080, 17, difficulty="hard")
    assert random.getstate() == before
    assert first == second
    assert intervening != first
    assert first is not second and first[0] is not second[0]
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(8080, 17, difficulty="hard") == second
