"""Focused regressions for the centroid-directed panel-permutation sampler."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "250925d67253"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

SEPARATORS = (0, 6, 12, 18)


def _bucket(value: float) -> int:
    return 0 if value < 1.5 else (1 if value <= 2.5 else 2)


def _nearest_anchor(value: float) -> int:
    return min(range(3), key=lambda index: abs(value - 2 * index))


def _background(grid):
    values = [grid[1][c] for c in range(1, 18) if grid[1][c] != 0]
    counts = Counter(values)
    return max(counts, key=counts.get)


def _marker_positions(grid, source, background=None):
    if background is None:
        background = _background(grid)
    br, bc = divmod(source, 3)
    r0, c0 = 1 + 6 * br, 1 + 6 * bc
    return [
        (r, c)
        for r in range(5)
        for c in range(5)
        if grid[r0 + r][c0 + c] != background
    ]


def _centroid_mapping(grid):
    bg = _background(grid)
    mapping = []
    for source in range(9):
        points = _marker_positions(grid, source, bg)
        row = sum(r for r, _ in points) / len(points)
        col = sum(c for _, c in points) / len(points)
        mapping.append(3 * _bucket(row) + _bucket(col))
    return mapping


def _bbox_mapping(grid):
    bg = _background(grid)
    mapping = []
    for source in range(9):
        points = _marker_positions(grid, source, bg)
        rows = [r for r, _ in points]
        cols = [c for _, c in points]
        row = (min(rows) + max(rows)) / 2
        col = (min(cols) + max(cols)) / 2
        mapping.append(3 * _bucket(row) + _bucket(col))
    return mapping


def _nearest_mapping(grid):
    bg = _background(grid)
    mapping = []
    for source in range(9):
        points = _marker_positions(grid, source, bg)
        row = sum(r for r, _ in points) / len(points)
        col = sum(c for _, c in points) / len(points)
        mapping.append(3 * _nearest_anchor(row) + _nearest_anchor(col))
    return mapping


def _median_mapping(grid):
    bg = _background(grid)
    mapping = []
    for source in range(9):
        points = _marker_positions(grid, source, bg)
        rows = sorted(r for r, _ in points)
        cols = sorted(c for _, c in points)

        def median(values):
            middle = len(values) // 2
            if len(values) % 2:
                return float(values[middle])
            return (values[middle - 1] + values[middle]) / 2

        mapping.append(3 * _bucket(median(rows)) + _bucket(median(cols)))
    return mapping


def intended_output(grid):
    """Independent mirror of the selected Racket authority."""
    mapping = _centroid_mapping(grid)
    assert sorted(mapping) == list(range(9))
    output = [[0] * 19 for _ in range(19)]
    for source, target in enumerate(mapping):
        sbr, sbc = divmod(source, 3)
        tbr, tbc = divmod(target, 3)
        sr0, sc0 = 1 + 6 * sbr, 1 + 6 * sbc
        tr0, tc0 = 1 + 6 * tbr, 1 + 6 * tbc
        for r in range(5):
            output[tr0 + r][tc0 : tc0 + 5] = grid[sr0 + r][sc0 : sc0 + 5]
    return output


def _components(points):
    remaining = set(points)
    found = []
    while remaining:
        first = remaining.pop()
        component = {first}
        stack = [first]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    stack.append(point)
        found.append(component)
    return found


def _nonbackground_components(grid):
    background = _background(grid)
    points = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != background
    }
    return _components(points)


def _uniform_cyclic(mapping):
    shifts = {(target - source) % 9 for source, target in enumerate(mapping)}
    return len(shifts) == 1


def test_rule_pin_and_public_contract():
    assert GEN.RULE_HASH == "9f1390aa0494"
    assert GEN.VERSION == "3.0.0"
    assert set(GEN.AXES) == {"permutation_kind", "marker_density", "palette_band"}
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.EXAMPLES_NEEDED == 4
    assert set(GEN.CANONICAL_SHORTCUTS) == {
        "bounding_box_center",
        "nearest_anchor",
        "median_marker",
    }


def test_canonical_inputs_are_accepted_and_independent_oracle_matches_answers():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 8
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert intended_output(pair["input"]) == pair["output"]


def test_declared_shortcuts_fit_every_canonical_pair():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    independent = {
        "bounding_box_center": _bbox_mapping,
        "nearest_anchor": _nearest_mapping,
        "median_marker": _median_mapping,
    }
    for name, mapping_fn in independent.items():
        assert all(mapping_fn(pair["input"]) == _centroid_mapping(pair["input"]) for pair in pairs)
        shortcut = GEN.CANONICAL_SHORTCUTS[name]
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("permutation_kind", ["derangement", "mixed_fixed"])
@pytest.mark.parametrize("marker_density", ["sparse", "dense"])
@pytest.mark.parametrize("palette_band", ["low", "high"])
def test_every_joint_override_is_exact_constructive_and_semantic(
    difficulty, permutation_kind, marker_density, palette_band
):
    grid = GEN.generate(
        271,
        13,
        difficulty=difficulty,
        permutation_kind=permutation_kind,
        marker_density=marker_density,
        palette_band=palette_band,
    )
    assert GEN.observe_overrides(grid) == {
        "permutation_kind": permutation_kind,
        "marker_density": marker_density,
        "palette_band": palette_band,
    }
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) == []
    assert intended_output(grid) != grid
    mapping = _centroid_mapping(grid)
    assert sorted(mapping) == list(range(9))
    assert not _uniform_cyclic(mapping)
    assert (sum(source == target for source, target in enumerate(mapping)) == 0) == (
        permutation_kind == "derangement"
    )
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert shortcut(grid) != intended_output(grid), name
    assert GEN.SEMANTIC_RIVALS["one_marker_global_shift"](grid) != intended_output(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"bogus": 1},
        {"permutation_kind": "rotation"},
        {"permutation_kind": 1},
        {"marker_density": "medium"},
        {"palette_band": "all"},
        {"palette_band": 1},
    ],
)
def test_invalid_and_unknown_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


@pytest.mark.parametrize("difficulty", ["simple", 1, True])
def test_invalid_difficulty_is_rejected(difficulty):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize(
    "seed,sample_index",
    [(True, 0), (0, True), (1.0, 0), (0, 1.0), ("1", 0), (0, "1"), (0, -1)],
)
def test_seed_and_sample_index_are_strict(seed, sample_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, sample_index)


def test_self_check_rejects_destructive_mutations():
    grid = GEN.generate(17, 23, marker_density="dense")
    mutations = []

    changed = deepcopy(grid)
    changed[0][1] = 4
    mutations.append(changed)

    changed = deepcopy(grid)
    for r in range(1, 6):
        for c in range(1, 6):
            changed[r][c] = _background(grid)
    mutations.append(changed)

    changed = deepcopy(grid)
    used = {value for row in grid for value in row}
    third = next(color for color in range(1, 10) if color not in used)
    changed[1][1] = third
    mutations.append(changed)

    changed = deepcopy(grid)
    changed.pop()
    mutations.append(changed)

    mutations.extend((None, [], [[]], [[0], [0, 1]], [[True] * 19 for _ in range(19)]))
    for malformed in mutations:
        assert GEN.self_check(malformed), malformed


def test_generated_morphology_is_canonical_like_and_separator_connected():
    marker_component_counts = set()
    for density in ("sparse", "dense"):
        for sample_index in range(40):
            grid = GEN.generate(811, sample_index, marker_density=density)
            assert len(_nonbackground_components(grid)) == 1
            total = 0
            for source in range(9):
                components = _components(_marker_positions(grid, source))
                total += len(components)
                assert all(
                    any(r in (0, 4) or c in (0, 4) for r, c in component)
                    for component in components
                )
            marker_component_counts.add(total)
    assert min(marker_component_counts) <= 17 <= max(marker_component_counts)
    assert len(marker_component_counts) >= 4


def test_default_sampling_is_replayable_diverse_and_refutes_every_rival():
    random.seed(8675309)
    state = random.getstate()
    unique = set()
    observed = set()
    for band in ("easy", "medium", "hard"):
        for index in range(64):
            grid = GEN.generate(911, index, difficulty=band)
            assert grid == GEN.generate(911, index, difficulty=band)
            assert random.getstate() == state
            assert GEN.self_check(grid) == []
            unique.add(repr(grid))
            observed.add(tuple(sorted(GEN.observe_overrides(grid).items())))
            truth = intended_output(grid)
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert rival(grid) != truth, (band, index, name)
    assert len(unique) >= 100
    assert len(observed) == 8


def test_four_demo_lessons_identify_all_declared_competitors_under_every_rotation():
    for band in ("easy", "medium", "hard"):
        pairs = []
        for index in range(5):
            grid = GEN.generate(1217, index, difficulty=band)
            pairs.append({"input": grid, "output": intended_output(grid)})
        for query_index in range(5):
            query = pairs[query_index]
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, query) == []
