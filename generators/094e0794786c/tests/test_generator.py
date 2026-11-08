"""Portable regression tests for the normalized two-shape XOR generator."""
from __future__ import annotations

from copy import deepcopy
import importlib
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "094e0794786c"


def _load_generator():
    selected = os.environ.get("GENERATOR_UNDER_TEST")
    if selected:
        path = Path(selected)
        if path.is_dir():
            path = path / "generator.py"
        spec = importlib.util.spec_from_file_location("generator_under_test", path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load generator from {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return importlib.import_module(
        "puzzle_generators.per_puzzle.094e0794786c.generator"
    )


gen = _load_generator()
CANONICAL = canonical_pairs(TASK_ID, root=find_root(__file__))


def _cells(grid, color):
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}


def _norm(cells):
    if not cells:
        return frozenset()
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return frozenset((r - min_r, c - min_c) for r, c in cells)


def _bbox_shape(cells):
    if not cells:
        return 0, 0
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _oracle(grid):
    first = _norm(_cells(grid, 1))
    second = _norm(_cells(grid, 2))
    xor = first ^ second
    if not xor:
        return [[0]]
    h = max(_bbox_shape(first)[0], _bbox_shape(second)[0])
    w = max(_bbox_shape(first)[1], _bbox_shape(second)[1])
    return [[8 if (r, c) in xor else 0 for c in range(w)] for r in range(h)]


def _components(cells):
    unseen = set(cells)
    count = 0
    while unseen:
        count += 1
        stack = [unseen.pop()]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    stack.append(point)
    return count


def _translated(grid, source_color, target_color, origin):
    """Paint a normalized copy of source_color as target_color at origin."""
    out = [row[:] for row in grid]
    for r, row in enumerate(out):
        for c, value in enumerate(row):
            if value == target_color:
                out[r][c] = 0
    shape = _norm(_cells(grid, source_color))
    for dr, dc in shape:
        out[origin[0] + dr][origin[1] + dc] = target_color
    return out


@pytest.mark.parametrize("pair", CANONICAL, ids=lambda pair: f"{pair['split']}{pair['pair_index']}")
def test_canonical_pairs_are_accepted_and_match_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert _oracle(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 8, "grid_w": 9, "n_cells_1": 3, "n_cells_2": 7},
        {"grid_h": 12, "grid_w": 14, "n_cells_1": 7, "n_cells_2": 3},
        {"grid_h": 9, "grid_w": 10, "n_cells_1": 5, "n_cells_2": 5},
    ],
)
def test_exact_overrides_are_observable_in_every_band(difficulty, overrides):
    grid = gen.generate(87, 19, difficulty=difficulty, **overrides)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == overrides
    assert _oracle(grid) != [[0]]


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"grid_h": 7},
        {"grid_h": 13},
        {"grid_w": 8},
        {"grid_w": 15},
        {"n_cells_1": 2},
        {"n_cells_1": 8},
        {"n_cells_2": 2},
        {"n_cells_2": 8},
        {"grid_h": True},
        {"n_cells_1": 3.0},
        {"n_cells_2": "4"},
    ],
)
def test_invalid_overrides_fail_loudly(overrides):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_generated_domain_is_two_connected_distinguishing_shapes(difficulty):
    for index in range(96):
        grid = gen.generate(1000 + index, index * 7, difficulty=difficulty)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(1000 + index, index * 7, difficulty=difficulty)
        assert {value for row in grid for value in row} <= {0, 1, 2}
        first, second = _cells(grid, 1), _cells(grid, 2)
        assert 3 <= len(first) <= 7
        assert 3 <= len(second) <= 7
        assert _components(first) == 1
        assert _components(second) == 1
        # Keep the two global objects visually separate, not merely color-separated.
        assert min(abs(r1 - r2) + abs(c1 - c2) for r1, c1 in first for r2, c2 in second) > 1
        n1, n2 = _norm(first), _norm(second)
        assert n1 & n2
        assert n1 - n2
        assert n2 - n1
        before = deepcopy(grid)
        assert _oracle(grid) != [[0]]
        assert grid == before


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_band_has_canonical_size_palette_support(difficulty):
    profiles = {
        (len(pair["input"]), len(pair["input"][0]), len({v for row in pair["input"] for v in row}))
        for pair in CANONICAL
    }
    seen = set()
    for seed in range(20):
        grid = gen.generate(seed, seed, difficulty=difficulty)
        seen.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
    assert seen & profiles


def test_validator_rejects_previous_off_domain_textures_and_impostors():
    empty = [[0] * 9 for _ in range(8)]
    one_color = deepcopy(empty)
    for r, c in ((1, 1), (1, 2), (2, 1)):
        one_color[r][c] = 1
    identical = deepcopy(one_color)
    for r, c in ((5, 5), (5, 6), (6, 5)):
        identical[r][c] = 2
    disconnected = deepcopy(identical)
    disconnected[5][6] = 0
    disconnected[7][8] = 2
    full = [[1] * 9 for _ in range(8)]
    singleton = deepcopy(empty)
    singleton[1][1] = 1
    singleton[6][7] = 2
    for bad in (empty, one_color, identical, disconnected, full, singleton):
        assert gen.self_check(bad)


def test_validator_rejects_palette_and_shape_mutations():
    grid = gen.generate(29, 4, grid_h=12, grid_w=14, n_cells_1=5, n_cells_2=6)
    unknown = deepcopy(grid)
    unknown[0][0] = 9
    assert gen.self_check(unknown)

    missing = deepcopy(grid)
    for r, row in enumerate(missing):
        for c, value in enumerate(row):
            if value == 2:
                missing[r][c] = 0
    assert gen.self_check(missing)

    # Replace red with a translated copy of blue, creating an empty XOR after normalization.
    identical = _translated(grid, 1, 2, (7, 8))
    assert gen.self_check(identical)


@pytest.mark.parametrize("seed", range(24))
def test_semantic_witnesses_refute_declared_rivals(seed):
    grid = gen.generate(400 + seed, seed)
    expected = _oracle(grid)
    assert gen.strict_canonical_like(grid) == []
    assert gen.SEMANTIC_WITNESSES["normalized_overlap"](grid) is True
    assert gen.SEMANTIC_WITNESSES["both_shapes_contribute"](grid) is True
    for rival in gen.LESSON_COMPETITORS.values():
        assert rival(grid) != expected


def test_lesson_identifiability_contract_accepts_generated_lesson():
    pairs = []
    for index in range(4):
        grid = gen.generate(700, index)
        pairs.append({"input": grid, "output": _oracle(grid)})
    assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_workspace_domain_probe_exhausts_declared_axis_product():
    path = Path(__file__).parents[1] / "workspace" / "domain_probe.py"
    spec = importlib.util.spec_from_file_location("domain_probe_under_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load domain probe from {path}")
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    report = probe.analyze(gen)
    assert report["axis_cases"] == 3000
    assert report["axis_failures"] == []
    assert report["shape_bank_sizes"] == {
        "3": 6,
        "4": 19,
        "5": 61,
        "6": 182,
        "7": 476,
    }
    assert report["all_size_pairs_have_distinguishing_shapes"] is True
