"""Regression tests for the first vertically-symmetric-object crop task."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "81fdfd815936"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _components4(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
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
    return sorted(
        components,
        key=lambda component: (
            min(row for row, _ in component[1]),
            min(col for _, col in component[1]),
        ),
    )


def _bbox(cells):
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def _is_lr_symmetric(cells):
    row0, col0, _, col1 = _bbox(cells)
    normalized = {(row - row0, col - col0) for row, col in cells}
    width = col1 - col0 + 1
    return all((row, width - 1 - col) in normalized for row, col in normalized)


def _crop(grid, component):
    _, cells = component
    row0, col0, row1, col1 = _bbox(cells)
    return [row[col0 : col1 + 1] for row in grid[row0 : row1 + 1]]


def _oracle(grid):
    symmetric = [component for component in _components4(grid) if _is_lr_symmetric(component[1])]
    assert symmetric
    return _crop(grid, symmetric[0])


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


def _candidate_sizes(grid):
    return [
        len(component[1])
        for component in _components4(grid)
        if _is_lr_symmetric(component[1])
    ]


def test_rule_hash_and_every_canonical_pair_are_accepted_and_solved():
    assert GEN.RULE_HASH == "320c881d146b"
    pairs = _canonical()
    assert len(pairs) == 3
    candidate_counts = []
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert _oracle(source) == pair["output"]
        assert source == pair["input"]
        candidate_counts.append(len(_candidate_sizes(source)))
    assert sorted(candidate_counts) == [1, 1, 2]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h,grid_w", [(10, 12), (12, 14)])
def test_exact_dimension_overrides_are_observable_in_every_band(band, grid_h, grid_w):
    grid = GEN.generate(1701, 7, difficulty=band, grid_h=grid_h, grid_w=grid_w)
    assert GEN.observe_overrides(grid) == {"grid_h": grid_h, "grid_w": grid_w}
    assert len(grid) == grid_h
    assert {len(row) for row in grid} == {grid_w}
    assert GEN.self_check(grid) == []
    assert GEN.rule_mirror(grid) == _oracle(grid)


@pytest.mark.parametrize(
    "args,kwargs",
    [
        ((True, 0), {}),
        ((1, True), {}),
        ((1, -1), {}),
        ((1, 0), {"bogus_axis": 1}),
        ((1, 0), {"grid_h": 9}),
        ((1, 0), {"grid_h": 13}),
        ((1, 0), {"grid_h": True}),
        ((1, 0), {"grid_w": 11}),
        ((1, 0), {"grid_w": 15}),
        ((1, 0), {"grid_w": 12.5}),
    ],
)
def test_invalid_calls_are_rejected(args, kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(*args, **kwargs)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="impossible")


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_generated_distribution_matches_the_three_object_canonical_domain(band):
    outputs = set()
    profiles = set()
    target_slots = set()
    for index in range(80):
        grid = GEN.generate(9000 + index, index, difficulty=band)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert grid == GEN.generate(9000 + index, index, difficulty=band)
        assert 10 <= len(grid) <= 12
        assert 12 <= len(grid[0]) <= 14

        components = _components4(grid)
        assert len(components) == 3
        assert len({color for color, _ in components}) == 3
        symmetric = [i for i, component in enumerate(components) if _is_lr_symmetric(component[1])]
        asymmetric = [i for i, component in enumerate(components) if not _is_lr_symmetric(component[1])]
        assert len(symmetric) == 2
        assert len(asymmetric) == 1
        target_slots.add(symmetric[0])
        profiles.add(GEN.schedule_profile(9000 + index, index, band))
        outputs.add(tuple(tuple(row) for row in GEN.rule_mirror(grid)))

    assert profiles == set(GEN.SCHEDULE_PROFILES)
    assert target_slots == {0, 1}
    assert len(outputs) >= 20


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_consecutive_lesson_and_rotation_refutes_all_declared_competitors(band):
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.LESSON_SCHEDULE_PERIOD == 2
    for start in range(12):
        pairs = []
        for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
            grid = GEN.generate(12000 + start, sample_index, difficulty=band)
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_declared_witnesses_are_real_counterexamples_and_shortcut_is_canonical_fitting():
    generated = [GEN.generate(4444, index, difficulty="medium") for index in range(2)]
    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        witness = GEN.SEMANTIC_WITNESSES[witness_name]
        fired = [grid for grid in generated if witness(grid)]
        assert fired, witness_name
        for grid in fired:
            assert any(
                GEN.SEMANTIC_RIVALS[rival_name](grid) != GEN.rule_mirror(grid)
                for rival_name in rival_names
            ), witness_name

    canonical = _canonical()
    assert set(GEN.CANONICAL_SHORTCUTS) == {"smallest_symmetric"}
    for shortcut in GEN.CANONICAL_SHORTCUTS.values():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in canonical)
        assert any(shortcut(grid) != GEN.rule_mirror(grid) for grid in generated)


def test_self_check_rejects_trivial_and_structural_impostors():
    valid = GEN.generate(555, 0, grid_h=10, grid_w=12)
    assert GEN.self_check(valid) == []

    all_background = [[0] * 12 for _ in range(10)]
    full_color = [[3] * 12 for _ in range(10)]
    singleton = [[0] * 12 for _ in range(10)]
    singleton[5][5] = 3

    only_two = copy.deepcopy(valid)
    _, removed = _components4(valid)[0]
    for row, col in removed:
        only_two[row][col] = 0

    duplicate_color = copy.deepcopy(valid)
    components = _components4(valid)
    old_color, recolored = components[1]
    new_color = components[0][0]
    assert old_color != new_color
    for row, col in recolored:
        duplicate_color[row][col] = new_color

    for name, grid in {
        "all_background": all_background,
        "full_color": full_color,
        "singleton": singleton,
        "only_two": only_two,
        "duplicate_color": duplicate_color,
    }.items():
        assert GEN.self_check(grid), name


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 12 for _ in range(10)]],
)
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
