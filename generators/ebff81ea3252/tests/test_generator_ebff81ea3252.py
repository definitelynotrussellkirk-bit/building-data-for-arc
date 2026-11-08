"""Focused regressions for the reviewed ebff81ea3252 input generator."""
from __future__ import annotations

import copy
import importlib.util
import os
from collections import deque
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs as read_canonical_pairs, find_root

TASK_ID = "ebff81ea3252"
HOME = Path(__file__).resolve().parents[1]
REPO_ROOT = find_root(__file__)


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_pairs() -> list[dict]:
    return [
        {"input": pair["input"], "output": pair["output"]}
        for pair in read_canonical_pairs(
            TASK_ID, root=REPO_ROOT, labeled_only=True
        )
    ]


def _components(grid: list[list[int]], color: int = 3) -> list[set[tuple[int, int]]]:
    height = len(grid)
    width = len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    found: list[set[tuple[int, int]]] = []
    while unseen:
        start = unseen.pop()
        component = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                point = (row + dr, col + dc)
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    queue.append(point)
        found.append(component)
    return found


def _centers(grid: list[list[int]]) -> list[tuple[int, int]]:
    result = []
    for row in range(1, len(grid) - 1):
        for col in range(1, len(grid[0]) - 1):
            cells = ((row, col), (row - 1, col), (row + 1, col),
                     (row, col - 1), (row, col + 1))
            if all(grid[r][c] == 3 for r, c in cells):
                result.append((row, col))
    return result


def _official_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent mirror of the selected five-cardinal-cell Racket predicate."""
    result = copy.deepcopy(grid)
    for row, col in _centers(grid):
        for r, c in ((row, col), (row - 1, col), (row + 1, col),
                     (row, col - 1), (row, col + 1)):
            result[r][c] = 7
    return result


def _target_component_sizes(grid: list[list[int]]) -> list[int]:
    centers = set(_centers(grid))
    sizes = []
    for component in _components(grid):
        if component & centers:
            sizes.append(len(component))
    return sorted(sizes)


def _five_cell_nonplus_count(grid: list[list[int]]) -> int:
    centers = set(_centers(grid))
    return sum(len(component) == 5 and not (component & centers)
               for component in _components(grid))


def test_rule_pin_unknown_override_and_canonical_acceptance() -> None:
    gen = _load_generator()
    assert gen.RULE_HASH == "deb3ac96cc89"
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)
    for pair in _canonical_pairs():
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert _official_output(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", (None, "easy", "medium", "hard"))
@pytest.mark.parametrize("context_mode", ("isolated", "attached"))
def test_every_exact_override_is_honored_in_every_band(
    band: str | None, context_mode: str
) -> None:
    gen = _load_generator()
    requested = {
        "grid_h": 8,
        "grid_w": 9,
        "n_pluses": 3,
        "context_mode": context_mode,
    }
    grid = gen.generate(734, 19, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert _five_cell_nonplus_count(grid) == 1
    expected_size = 5 if context_mode == "isolated" else 6
    assert _target_component_sizes(grid) == [expected_size] * 3


@pytest.mark.parametrize(
    "key,value",
    (("grid_h", 7), ("grid_h", 12), ("grid_w", 8), ("grid_w", 12),
     ("n_pluses", 0), ("n_pluses", 4),
     ("context_mode", "mixed"), ("n_pluses", True)),
)
def test_invalid_override_values_are_rejected(key: str, value: object) -> None:
    gen = _load_generator()
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


def test_declared_shortcuts_fit_canonical_and_generated_witnesses_refute_them() -> None:
    gen = _load_generator()
    pairs = _canonical_pairs()
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "component_exact_only",
        "size_five_components",
    }
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name

    attached = gen.generate(91, 7, grid_h=8, grid_w=9,
                            n_pluses=2, context_mode="attached")
    official = _official_output(attached)
    assert gen.SEMANTIC_WITNESSES["attached_target"](attached)
    assert gen.SEMANTIC_RIVALS["component_exact_only"](attached) != official
    assert gen.SEMANTIC_RIVALS["size_five_components"](attached) != official

    isolated = gen.generate(92, 8, grid_h=8, grid_w=9,
                            n_pluses=2, context_mode="isolated")
    official = _official_output(isolated)
    assert gen.SEMANTIC_WITNESSES["five_cell_nonplus"](isolated)
    assert gen.SEMANTIC_RIVALS["size_five_components"](isolated) != official


def test_default_distribution_is_deterministic_diverse_and_covers_both_contexts() -> None:
    gen = _load_generator()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        contexts = set()
        plus_counts = set()
        signatures = set()
        for index in range(96):
            seed = 12000 + 1000 * band_index + index
            grid = gen.generate(seed, index * 11 + 3, difficulty=band)
            assert grid == gen.generate(seed, index * 11 + 3, difficulty=band)
            assert gen.self_check(grid) == []
            observed = gen.observe_overrides(grid)
            contexts.add(observed["context_mode"])
            plus_counts.add(observed["n_pluses"])
            signatures.add(tuple(map(tuple, grid)))
        assert contexts == {"isolated", "attached"}
        assert plus_counts == {1, 2, 3}
        assert len(signatures) >= 90


@pytest.mark.parametrize("grid", (None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(8)]))
def test_self_check_reports_malformed_inputs_without_raising(grid) -> None:
    gen = _load_generator()
    assert gen.self_check(grid)
