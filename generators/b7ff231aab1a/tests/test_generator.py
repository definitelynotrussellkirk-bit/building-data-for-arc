"""Regression tests for the marker-count / area-rank generator repair."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import itertools
import os
from pathlib import Path
import random

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "b7ff231aab1a"
RULE_HASH = "5c4099040cb4"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
_spec = importlib.util.spec_from_file_location("generator_under_test", GENERATOR_PATH)
assert _spec is not None and _spec.loader is not None
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            seen.add((r, c))
            stack = [(r, c)]
            comp = []
            while stack:
                rr, cc = stack.pop()
                comp.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(comp)
    return result


def _render_selected(grid, comp):
    rows = [r for r, _ in comp]
    cols = [c for _, c in comp]
    r0, r1 = min(rows), max(rows)
    c0, c1 = min(cols), max(cols)
    cropped = [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]
    return [
        [8 if cropped[r // 2][c // 2] != 0 else 0 for c in range(2 * len(cropped[0]))]
        for r in range(2 * len(cropped))
    ]


def _area_rule(grid):
    comps = sorted(
        _components(grid, 1),
        key=lambda comp: (len(comp), min(r for r, _ in comp), min(c for _, c in comp)),
    )
    k = sum(value == 9 for row in grid for value in row)
    return _render_selected(grid, comps[k - 1])


def _reading_order_rule(grid):
    comps = sorted(
        _components(grid, 1),
        key=lambda comp: (min(r for r, _ in comp), min(c for _, c in comp)),
    )
    k = sum(value == 9 for row in grid for value in row)
    return _render_selected(grid, comps[k - 1])


def _pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def test_rule_pin_and_canonical_authority_are_preserved():
    assert gen.VERSION == "2.0.0"
    assert gen.RULE_HASH == RULE_HASH
    pairs = _pairs()
    assert len(pairs) == 6
    for pair in pairs:
        grid = deepcopy(pair["input"])
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert _area_rule(grid) == pair["output"]
        assert gen.rule_mirror(grid) == pair["output"]


def test_declared_reading_order_shortcut_fits_all_canonical_pairs():
    assert set(gen.CANONICAL_SHORTCUTS) == {"reading_order_rank"}
    assert set(gen.LESSON_COMPETITORS) == {
        "reading_order_rank",
        "always_smallest",
        "always_middle",
        "always_largest",
    }
    for pair in _pairs():
        assert _reading_order_rule(pair["input"]) == pair["output"]
        assert gen.CANONICAL_SHORTCUTS["reading_order_rank"](pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_default_curriculum_is_lawful_observable_and_adversarial(difficulty):
    for seed in (0, 1, 99173):
        for sample_index in range(30):
            grid = gen.generate(seed, sample_index, difficulty=difficulty)
            assert gen.self_check(grid) == []
            observed = gen.observe_overrides(grid)
            assert set(observed) == set(gen.AXES)
            assert observed["marker_count"] == sample_index % 3 + 1
            assert gen.rule_mirror(grid) == _area_rule(grid)
            assert gen.SEMANTIC_WITNESSES["size_rank_not_position"](grid)
            assert gen.SEMANTIC_RIVALS["reading_order_rank"](grid) != _area_rule(grid)
            markers = _components(grid, 9)
            assert len(markers) == 1
            assert len(markers[0]) == observed["marker_count"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_all_exact_override_combinations_are_observable(difficulty):
    values = {
        "grid_h": (11, 12),
        "grid_w": (15, 16, 17),
        "marker_count": (1, 2, 3),
        "size_profile": tuple(gen.SIZE_PROFILES),
        "rank_layout": tuple(gen.RANK_LAYOUTS),
    }
    keys = tuple(values)
    for index, combo in enumerate(itertools.product(*(values[key] for key in keys))):
        requested = dict(zip(keys, combo, strict=True))
        grid = gen.generate(
            40000 + index,
            index,
            difficulty=difficulty,
            **requested,
        )
        assert gen.self_check(grid) == [], requested
        assert gen.observe_overrides(grid) == requested
        assert gen.rule_mirror(grid) == _area_rule(grid)
        assert gen.SEMANTIC_WITNESSES["size_rank_not_position"](grid)


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"grid_h": 10},
        {"grid_h": 13},
        {"grid_w": 14},
        {"grid_w": 18},
        {"marker_count": 0},
        {"marker_count": 4},
        {"size_profile": "not-a-profile"},
        {"rank_layout": "small_medium_large"},
        {"grid_h": True},
        {"grid_w": 16.0},
        {"marker_count": "2"},
    ],
)
def test_invalid_overrides_are_rejected_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, **overrides)


def test_invalid_difficulty_is_rejected_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 2, difficulty="impossible")


def test_three_consecutive_demos_identify_the_lesson_for_every_cyclic_start():
    assert gen.EXAMPLES_NEEDED == 3
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in (7, 7007):
            for start in range(gen.LESSON_SCHEDULE_PERIOD):
                grids = [
                    gen.generate(seed, start + offset, difficulty=difficulty)
                    for offset in range(4)
                ]
                demos = [
                    {"input": grid, "output": _area_rule(grid)}
                    for grid in grids[:3]
                ]
                query = {"input": grids[3], "output": _area_rule(grids[3])}
                assert gen.lesson_identifiable(demos, query) == []
                assert {gen.observe_overrides(d["input"])["marker_count"] for d in demos} == {1, 2, 3}
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(rival(d["input"]) != d["output"] for d in demos), name


def test_lesson_contract_rejects_incomplete_or_mislabeled_demonstrations():
    grids = [gen.generate(11, index) for index in range(4)]
    demos = [{"input": grid, "output": _area_rule(grid)} for grid in grids[:3]]
    query = {"input": grids[3], "output": _area_rule(grids[3])}
    assert gen.lesson_identifiable(demos[:2], query)
    damaged = deepcopy(demos)
    damaged[0]["output"] = [[0]]
    assert gen.lesson_identifiable(damaged, query)


def test_generation_is_fresh_deterministic_and_global_rng_pure():
    random.seed(20261007)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert first != second


def test_self_check_rejects_structural_corruption_without_mutating_inputs():
    grid = gen.generate(3, 4)
    original = deepcopy(grid)
    assert gen.self_check(grid) == []
    assert grid == original

    corruptions = {}
    corruptions["ragged"] = deepcopy(grid)
    corruptions["ragged"][-1].pop()
    corruptions["bad_color"] = deepcopy(grid)
    corruptions["bad_color"][0][0] = 7
    corruptions["no_markers"] = [[0 if value == 9 else value for value in row] for row in grid]
    corruptions["split_markers"] = deepcopy(gen.generate(9, 1, marker_count=2))
    marker_cells = [(r, c) for r, row in enumerate(corruptions["split_markers"]) for c, value in enumerate(row) if value == 9]
    corruptions["split_markers"][marker_cells[1][0]][marker_cells[1][1]] = 0
    corruptions["split_markers"][0][-1] = 9
    corruptions["merge_components"] = deepcopy(grid)
    comps = _components(corruptions["merge_components"], 1)
    (r0, c0), (r1, c1) = comps[0][0], comps[1][0]
    # This mutation need not connect the exact original two; painting a path
    # always violates the exact component/profile grammar one way or another.
    rr, cc = r0, c0
    while rr != r1:
        rr += 1 if r1 > rr else -1
        corruptions["merge_components"][rr][cc] = 1
    while cc != c1:
        cc += 1 if c1 > cc else -1
        corruptions["merge_components"][rr][cc] = 1

    for name, damaged in corruptions.items():
        assert gen.self_check(damaged), name


def test_workspace_reference_probe_matches_rule_and_declared_shortcut():
    import sys

    workspace = str(HOME / "workspace")
    if workspace not in sys.path:
        sys.path.insert(0, workspace)
    import reference_probe

    grid = gen.generate(
        20261007,
        0,
        grid_h=11,
        grid_w=15,
        marker_count=1,
        size_profile="sizes_234",
        rank_layout="medium_large_small",
    )
    report = reference_probe.analyze(grid)
    assert report["intended_output"] == gen.rule_mirror(grid)
    assert report["reading_order_output"] == gen.CANONICAL_SHORTCUTS["reading_order_rank"](grid)
    assert report["intended_output"] != report["reading_order_output"]
    assert report["marker_count"] == 1
    assert report["size_order"] == [2, 3, 4]
    assert report["reading_order_size_ranks"] == [2, 3, 1]
