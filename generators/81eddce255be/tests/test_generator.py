"""Portable regression suite for the header-count area selector."""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "81eddce255be"
HOME = Path(__file__).resolve().parents[1]
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}_generator", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _components(grid):
    """Independent same-color four-connected body components, row-major."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r0 in range(1, h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            queue = deque([(r0, c0)])
            seen.add((r0, c0))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in CARDINAL:
                    nr, nc = r + dr, c + dc
                    if (
                        1 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append({"color": color, "cells": tuple(sorted(cells))})
    result.sort(key=lambda obj: min(obj["cells"]))
    return result


def _rule_output(grid):
    k = sum(value == 1 for value in grid[0])
    out = [[0 for _ in row] for row in grid]
    for component in _components(grid):
        if len(component["cells"]) == k:
            for r, c in component["cells"]:
                out[r][c] = component["color"]
    return out


def _topmost_output(grid):
    out = [[0 for _ in row] for row in grid]
    components = _components(grid)
    if components:
        component = components[0]
        for r, c in component["cells"]:
            out[r][c] = component["color"]
    return out


def _observed(grid):
    components = _components(grid)
    k = sum(value == 1 for value in grid[0])
    matches = [index for index, obj in enumerate(components) if len(obj["cells"]) == k]
    assert len(matches) == 1
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "K": k,
        "target_rank": matches[0],
    }


def _target_size_rank(grid):
    components = _components(grid)
    k = sum(value == 1 for value in grid[0])
    return sorted(len(obj["cells"]) for obj in components).index(k)


def test_rule_pin_and_every_canonical_pair():
    assert gen.RULE_HASH == "70441dae68b0"
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert _rule_output(pair["input"]) == pair["output"]
        assert gen.oracle_output(deepcopy(pair["input"])) == pair["output"]


def test_historical_dead_override_and_no_marker_validator_defects_are_closed():
    grid = gen.generate(123, 0, difficulty="easy", K=6)
    assert sum(value == 1 for value in grid[0]) == 6
    assert gen.observe_overrides(grid)["K"] == 6
    assert gen.self_check(grid) == []

    arbitrary = [[9] * 10 for _ in range(9)]
    findings = gen.self_check(arbitrary)
    assert findings
    assert any("header" in finding or "row 0" in finding for finding in findings)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 10, "grid_w": 10, "K": 2, "target_rank": 0},
        {"grid_h": 10, "grid_w": 14, "K": 6, "target_rank": 2},
        {"grid_h": 14, "grid_w": 10, "K": 3, "target_rank": 1},
        {"grid_h": 14, "grid_w": 14, "K": 5, "target_rank": 0},
    ],
)
def test_exact_controls_are_constructive_and_observable_in_every_band(band, options):
    grid = gen.generate(71, 19, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert _observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert gen.oracle_output(deepcopy(grid)) == _rule_output(grid)


@pytest.mark.parametrize(
    "difficulty,options",
    [
        (None, {"typo": 1}),
        (None, {"palette_kind": "warm"}),
        (None, {"texture": "no_markers"}),
        (None, {"grid_h": 9}),
        (None, {"grid_h": 15}),
        (None, {"grid_w": 9}),
        (None, {"grid_w": 15}),
        (None, {"K": 1}),
        (None, {"K": 7}),
        (None, {"target_rank": -1}),
        (None, {"target_rank": 3}),
        (None, {"K": True}),
        (None, {"K": 3.0}),
        (None, {"grid_w": "10"}),
        ("expert", {}),
    ],
)
def test_invalid_or_unknown_controls_are_loud(difficulty, options):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty=difficulty, **options)


def test_default_distribution_covers_profiles_counts_ranks_and_is_deterministic():
    canonical_profiles = {(10, 10, 5), (11, 11, 5), (12, 12, 5)}
    profiles = set()
    counts = set()
    target_ranks = set()
    target_size_ranks = set()
    colors = set()
    shapes = set()

    for band in ("easy", "medium", "hard"):
        for index in range(60):
            grid = gen.generate(3100 + index, index, difficulty=band)
            assert grid == gen.generate(3100 + index, index, difficulty=band)
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            assert gen.oracle_output(deepcopy(grid)) == _rule_output(grid)
            observed = gen.observe_overrides(grid)
            profiles.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
            counts.add(observed["K"])
            target_ranks.add(observed["target_rank"])
            target_size_ranks.add(_target_size_rank(grid))
            for component in _components(grid):
                colors.add(component["color"])
                r0 = min(r for r, _ in component["cells"])
                c0 = min(c for _, c in component["cells"])
                shapes.add(tuple(sorted((r - r0, c - c0) for r, c in component["cells"])))

    assert profiles == canonical_profiles
    assert counts == {2, 3, 4, 5, 6}
    assert target_ranks == {0, 1, 2}
    assert target_size_ranks == {0, 1, 2}
    assert colors == set(range(2, 10))
    assert len(shapes) >= 12


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 10 for _ in range(10)],
        [[0] * 10 for _ in range(10)],
        [[9] * 10 for _ in range(10)],
        [[1, 1] + [0] * 8, [1] + [0] * 9] + [[0] * 10 for _ in range(8)],
        [[1, 1] + [0] * 8, [0] * 10, [0, 1] + [0] * 8] + [[0] * 10 for _ in range(7)],
    ],
)
def test_self_check_is_total_and_rejects_malformed_or_impostor_inputs(grid):
    assert gen.self_check(deepcopy(grid))


def test_self_check_rejects_structural_mutations():
    base = gen.generate(41, 7, K=4, target_rank=1)
    assert gen.self_check(base) == []

    mutations = []

    no_header = deepcopy(base)
    no_header[0] = [0] * len(no_header[0])
    mutations.append(no_header)

    dirty_separator = deepcopy(base)
    dirty_separator[1][0] = 2
    mutations.append(dirty_separator)

    body_marker = deepcopy(base)
    body_marker[2][0] = 1
    mutations.append(body_marker)

    removed_component = deepcopy(base)
    first = _components(removed_component)[0]
    for r, c in first["cells"]:
        removed_component[r][c] = 0
    mutations.append(removed_component)

    duplicate_target_size = deepcopy(base)
    components = _components(duplicate_target_size)
    distractor = next(obj for obj in components if len(obj["cells"]) != 4)
    cells = list(distractor["cells"])
    while len(cells) > 4:
        r, c = cells.pop()
        duplicate_target_size[r][c] = 0
    mutations.append(duplicate_target_size)

    for changed in mutations:
        assert gen.self_check(changed)


def test_canonical_topmost_shortcut_is_declared_and_refuted_by_generated_witness():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert all(_topmost_output(pair["input"]) == pair["output"] for pair in pairs)

    grid = gen.generate(19, 5, K=4, target_rank=2)
    expected = _rule_output(grid)
    assert gen.SEMANTIC_WITNESSES["non_topmost_target"](grid)
    assert gen.SEMANTIC_RIVALS["topmost_object"](deepcopy(grid)) == _topmost_output(grid)
    assert gen.SEMANTIC_RIVALS["topmost_object"](deepcopy(grid)) != expected
    assert gen.CANONICAL_SHORTCUTS["topmost_object"](deepcopy(grid)) != expected
    assert gen.LESSON_COMPETITORS["topmost_object"](deepcopy(grid)) != expected


def test_every_three_consecutive_default_demos_refute_topmost_shortcut():
    rival = gen.LESSON_COMPETITORS["topmost_object"]
    for band in ("easy", "medium", "hard"):
        for start in range(15):
            demos = []
            for index in range(start, start + 3):
                grid = gen.generate(991, index, difficulty=band)
                demos.append((grid, _rule_output(grid)))
            assert any(rival(deepcopy(grid)) != output for grid, output in demos)

@pytest.mark.parametrize("sample_index", [True, False, -1, 1.0, "1"])
def test_invalid_sample_index_is_loud(sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(991, sample_index, difficulty="easy")


def test_difficulty_is_a_live_nuisance_without_changing_public_controls():
    grids = {
        band: gen.generate(727, 8, difficulty=band)
        for band in ("easy", "medium", "hard")
    }
    assert len({repr(grid) for grid in grids.values()}) == 3
    assert len({_observed(grid).items().__repr__() for grid in grids.values()}) == 1


def test_generated_header_matches_canonical_single_object_signature():
    for band in ("easy", "medium", "hard"):
        for index in range(30):
            grid = gen.generate(8800 + index, index, difficulty=band)
            columns = [c for c, value in enumerate(grid[0]) if value == 1]
            assert columns == list(range(columns[0], columns[0] + len(columns)))
            assert len(columns) >= 2
