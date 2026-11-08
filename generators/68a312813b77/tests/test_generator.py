"""Source-bound regressions for the 8-connected bbox-fill generator."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location("generator_under_test", SOURCE)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

TASK_ID = "68a312813b77"


def _canonical_row() -> dict:
    from reviewer_support import canonical_path, find_root

    with canonical_path(find_root(__file__)).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise KeyError(TASK_ID)


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    return [pair for split in ("train", "test") for pair in row[split]]


def _components8(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    components = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component = [start]
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == dc == 0:
                        continue
                    neighbor = (r + dr, c + dc)
                    if neighbor in unseen:
                        unseen.remove(neighbor)
                        component.append(neighbor)
                        stack.append(neighbor)
        components.append(sorted(component))
    return components


def _bbox(component: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in component]
    cols = [c for _, c in component]
    return min(rows), min(cols), max(rows), max(cols)


def _touches_boundary(box: tuple[int, int, int, int], h: int, w: int) -> bool:
    r0, c0, r1, c1 = box
    return r0 == 0 or c0 == 0 or r1 == h - 1 or c1 == w - 1


def _fill_selected(
    grid: list[list[int]],
    predicate,
) -> list[list[int]]:
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    for component in _components8(grid):
        box = _bbox(component)
        if not predicate(box, h, w):
            continue
        r0, c0, r1, c1 = box
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if out[r][c] == 0:
                    out[r][c] = 7
    return out


def _rule_output(grid: list[list[int]]) -> list[list[int]]:
    return _fill_selected(grid, lambda box, h, w: True)


def _skip_boundary_rival(grid: list[list[int]]) -> list[list[int]]:
    return _fill_selected(grid, lambda box, h, w: not _touches_boundary(box, h, w))


def _boundary_only_rival(grid: list[list[int]]) -> list[list[int]]:
    return _fill_selected(grid, lambda box, h, w: _touches_boundary(box, h, w))


def _global_bbox_rival(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    nonzero = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    if not nonzero:
        return out
    r0, c0, r1, c1 = _bbox(nonzero)
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if out[r][c] == 0:
                out[r][c] = 7
    return out


def test_rule_hash_is_pinned_to_the_selected_canonical_program():
    assert GEN.RULE_HASH == "0515ffa9320e"


def test_canonical_pairs_are_accepted_and_match_independent_oracle():
    for pair in _canonical_pairs():
        original = deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert _rule_output(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_every_default_sample_contains_boundary_and_interior_components():
    for band in (None, "easy", "medium", "hard"):
        for index in range(24):
            grid = GEN.generate(10_000 + index, index, difficulty=band)
            assert GEN.self_check(grid) == []
            h, w = len(grid), len(grid[0])
            flags = [_touches_boundary(_bbox(comp), h, w) for comp in _components8(grid)]
            assert True in flags
            assert False in flags


def test_every_default_sample_refutes_boundary_and_global_bbox_shortcuts():
    for band in (None, "easy", "medium", "hard"):
        for index in range(24):
            grid = GEN.generate(20_000 + index, index, difficulty=band)
            truth = _rule_output(grid)
            assert _skip_boundary_rival(grid) != truth
            assert _boundary_only_rival(grid) != truth
            assert _global_bbox_rival(grid) != truth


def test_exact_object_count_is_realized_or_rejected_loudly():
    grid = GEN.generate(31, 4, grid_h=20, grid_w=20, n_objects=5)
    assert len(_components8(grid)) == 5
    with pytest.raises(ValueError, match="fit|capacity|place"):
        GEN.generate(31, 4, grid_h=6, grid_w=6, n_objects=5)


@pytest.mark.parametrize(
    ("difficulty", "kwargs"),
    [
        ("easy", {"grid_h": 6}),
        ("easy", {"grid_w": 6}),
        ("easy", {"n_objects": 5}),
        ("easy", {"size_distribution": "large"}),
        ("medium", {"grid_h": 6}),
        ("medium", {"grid_w": 6}),
        ("medium", {"n_objects": 5}),
        ("hard", {"grid_h": 6}),
        ("hard", {"grid_w": 6}),
    ],
)
def test_declared_single_axis_geometry_controls_are_realizable(difficulty, kwargs):
    for seed in range(3):
        grid = GEN.generate(seed, seed * 17 + 3, difficulty=difficulty, **kwargs)
        assert GEN.self_check(grid) == []
        if "grid_h" in kwargs:
            assert len(grid) == kwargs["grid_h"]
        if "grid_w" in kwargs:
            assert len(grid[0]) == kwargs["grid_w"]
        if "n_objects" in kwargs:
            assert len(_components8(grid)) == kwargs["n_objects"]
        if kwargs.get("size_distribution") == "large":
            assert all(
                _bbox(component)[2] - _bbox(component)[0] + 1 == 5
                and _bbox(component)[3] - _bbox(component)[1] + 1 == 5
                for component in _components8(grid)
            )


def test_impossible_joint_geometry_reports_the_conflicting_axes():
    with pytest.raises(ValueError, match="fit|place|feasible") as caught:
        GEN.generate(
            7,
            2,
            grid_h=6,
            grid_w=6,
            n_objects=5,
            size_distribution="large",
        )
    assert set(caught.value.incompatible_axes) == {
        "grid_h",
        "grid_w",
        "n_objects",
        "size_distribution",
    }


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0, 0], [0]],
        [[0, 0], [0, 0]],
        [[4, 4], [4, 4]],
        [[4, 0, 4]],
        [[7, 7, 0], [7, 0, 0]],
        [[True, 0], [0, 0]],
        [[10, 0], [0, 0]],
    ],
)
def test_validator_rejects_malformed_or_non_teaching_scenes(grid):
    assert GEN.self_check(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"difficulty": "expert"},
        {"typo_axis": 1},
        {"grid_h": True},
        {"grid_w": 21},
        {"n_objects": 0},
        {"n_objects": 6},
        {"fg_color": 0},
        {"fg_color": 7},
        {"object_kind": "triangle"},
    ],
)
def test_invalid_public_controls_fail_closed(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, **kwargs)


def test_named_rivals_are_refuted_and_lesson_gate_is_clean():
    assert GEN.CANONICAL_SHORTCUTS == {}
    assert set(GEN.SEMANTIC_RIVALS) >= {
        "skip_boundary",
        "boundary_only",
        "global_bbox",
    }
    grids = [GEN.generate(50_000, index) for index in range(4)]
    pairs = [{"input": grid, "output": _rule_output(grid)} for grid in grids]
    for query_index in range(4):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert GEN.lesson_identifiable(demos, pairs[query_index]) == []


def test_rule_mirror_is_pure_and_matches_independent_oracle():
    for index in range(16):
        grid = GEN.generate(55_000 + index, index)
        original = deepcopy(grid)
        assert GEN.rule_mirror(grid) == _rule_output(grid)
        assert grid == original


def test_real_racket_matches_independent_oracle_on_boundary_surfaces():
    from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
    from puzzle_generators.rule_wrap import wrap_rule

    def rule_application(source, grid):
        rows = " ".join("(" + " ".join(str(value) for value in row) + ")" for row in grid)
        return f"({wrap_rule(source)} '({rows}))"

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    source = _canonical_row()["program_solution"]
    grids = [GEN.generate(60_000 + index, index) for index in range(8)]
    bridge = RacketBridge(max_calls_before_restart=16)
    try:
        for grid in grids:
            original = deepcopy(grid)
            assert bridge.eval_text(rule_application(source, grid)) == _rule_output(grid)
            assert grid == original
    finally:
        bridge.shutdown()
