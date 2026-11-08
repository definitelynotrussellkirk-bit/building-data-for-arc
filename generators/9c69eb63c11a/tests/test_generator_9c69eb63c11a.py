"""Focused regressions for the median-area-object generator repair."""
from __future__ import annotations

import copy
import random
from collections import deque

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "9c69eb63c11a"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _components(grid):
    """Return nonzero 4-connected components as lists of cells."""
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    out = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    queue.append(point)
        out.append(cells)
    return out


def _facts(grid):
    components = _components(grid)
    colors = {grid[r][c] for component in components for r, c in component}
    return {
        "shape": (len(grid), len(grid[0])),
        "component_count": len(components),
        "component_sizes": sorted(len(component) for component in components),
        "colors": colors,
    }


def test_metadata_describes_only_truthful_independent_controls():
    assert GEN.GENERATOR_ID == GEN.TASK_ID == TASK_ID
    assert GEN.RULE_HASH == "e0d91c9e70a7"
    assert GEN.EXAMPLES_NEEDED >= 2
    assert set(GEN.AXES) == {"grid_h", "grid_w", "n_blobs", "palette_kind"}
    assert GEN.AXES["n_blobs"]["valid"] == "3|5"
    assert GEN.HELPFUL_TEXTURES == GEN.DEGENERATE_TEXTURES == ()
    assert GEN.LAWFUL_DEGENERATE_TEXTURES == ()


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_exact_five_blob_boundary_overrides_round_trip(difficulty):
    requested = {
        "grid_h": 14,
        "grid_w": 14,
        "n_blobs": 5,
        "palette_kind": "warm",
    }
    grid = GEN.generate(20261008, 19, difficulty=difficulty, **requested)
    facts = _facts(grid)
    assert facts["shape"] == (14, 14)
    assert facts["component_count"] == 5
    assert len(set(facts["component_sizes"])) == 5
    assert len(facts["colors"]) == 5
    assert GEN.self_check(grid, difficulty=difficulty) == []
    observed = GEN.observe_overrides(grid)
    assert {key: observed[key] for key in requested} == requested


def test_smallest_declared_grid_still_constructs_five_isolated_blobs():
    for seed in range(20):
        grid = GEN.generate(
            seed,
            seed,
            grid_h=8,
            grid_w=8,
            n_blobs=5,
            palette_kind="cool",
        )
        facts = _facts(grid)
        assert facts["shape"] == (8, 8)
        assert facts["component_count"] == 5
        assert facts["component_sizes"] == [1, 2, 3, 4, 5]
        assert GEN.self_check(grid) == []


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_default_lesson_schedule_keeps_every_two_demo_window_identifiable(difficulty):
    counts = []
    for index in range(8):
        grid = GEN.generate(44617, index, difficulty=difficulty)
        assert GEN.self_check(grid, difficulty=difficulty) == []
        counts.append(len(_components(grid)))
    assert counts == [5, 5, 3, 5, 5, 3, 5, 5]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo_axis": 1},
        {"palette_size": 5},
        {"n_distinct_colors": 5},
        {"position_bias": "spread"},
        {"size_spread": "distinct"},
        {"grid_h": 7},
        {"grid_w": 15},
        {"n_blobs": 4},
        {"n_blobs": True},
        {"palette_kind": "unknown"},
        {"texture": "solid"},
    ],
)
def test_unknown_retired_or_invalid_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


def test_canonical_inputs_remain_inside_validator_domain():
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize(
    "args, kwargs",
    [
        ((True, 0), {}),
        ((1.0, 0), {}),
        (("1", 0), {}),
        ((0, True), {}),
        ((0, 1.0), {}),
        ((0, -1), {}),
        ((0, 0), {"difficulty": True}),
        ((0, 0), {"difficulty": 0}),
        ((0, 0), {"difficulty": 1.0}),
        ((0, 0), {"difficulty": "__invalid_difficulty__"}),
    ],
)
def test_invalid_call_scalars_are_rejected(args, kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(*args, **kwargs)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_two_demo_schedule_is_semantically_identifiable(difficulty):
    for start in range(8):
        demos = []
        for index in range(start, start + GEN.EXAMPLES_NEEDED):
            grid = GEN.generate(90210, index, difficulty=difficulty)
            demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
        query_grid = GEN.generate(90211, start + GEN.EXAMPLES_NEEDED, difficulty=difficulty)
        assert GEN.lesson_identifiable(demos, {"input": query_grid}) == []
        assert any(
            GEN.SEMANTIC_WITNESSES["five_blobs_refute_second_largest"](demo["input"])
            for demo in demos
        )
        assert any(
            GEN.LESSON_COMPETITORS["second_largest_object"](demo["input"])
            != demo["output"]
            for demo in demos
        )


def test_lesson_contract_rejects_only_three_blob_or_mislabeled_demos():
    three = GEN.generate(77, 0, n_blobs=3)
    three_demos = [
        {"input": three, "output": GEN.rule_mirror(three)},
        {"input": GEN.generate(78, 2, n_blobs=3), "output": None},
    ]
    three_demos[1]["output"] = GEN.rule_mirror(three_demos[1]["input"])
    query = {"input": GEN.generate(79, 3)}
    reasons = GEN.lesson_identifiable(three_demos, query)
    assert any("second-largest" in reason for reason in reasons)

    poisoned = copy.deepcopy(three_demos)
    poisoned[0]["output"] = poisoned[0]["input"]
    reasons = GEN.lesson_identifiable(poisoned, query)
    assert any("output" in reason for reason in reasons)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_generation_is_deterministic_fresh_and_global_rng_pure(difficulty):
    state = random.getstate()
    first = GEN.generate(1234, 5, difficulty=difficulty)
    pristine = copy.deepcopy(first)
    first[0][0] = 9 if first[0][0] != 9 else 1
    second = GEN.generate(1234, 5, difficulty=difficulty)
    assert second == pristine
    assert second is not first
    assert all(a is not b for a, b in zip(second, first))
    assert random.getstate() == state
