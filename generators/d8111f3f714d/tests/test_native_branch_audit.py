"""Independent geometry and executable-rival checks for the native family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest


PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/audit_native.py"
SPEC = importlib.util.spec_from_file_location("_branch_audit_test", PATH)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def scene():
    grid = [[0] * 22 for _ in range(20)]
    for r, c in [(2, 5), (18, 5), (3, 0), (5, 2), (7, 8), (9, 10),
                 (11, 12), (13, 14), (15, 16), (17, 19)]:
        grid[r][c] = 2
    return grid


def transpose(grid):
    return [list(row) for row in zip(*grid)]


def test_independent_geometry_derives_unique_trunk_and_all_eight_branches():
    facts = AUDIT.analyze_scene(scene())
    assert facts["orientation"] == "v"
    assert facts["trunk_line"] == 5
    assert facts["trunk_span"] == [2, 18]
    assert len(facts["branches"]) == 8
    assert facts["side_counts"] == {"negative": 2, "positive": 6}


@pytest.mark.parametrize("setting", ["toward_trunk", "away_to_edge"])
def test_independent_renderer_matches_hand_derived_rows_and_preserves_reds(setting):
    grid = scene()
    output = AUDIT.independent_apply(grid, {"branch_direction": setting})
    expected_row = list(grid[7])
    expected_row[5] = 3
    for c in (range(6, 8) if setting == "toward_trunk" else range(9, 22)):
        expected_row[c] = 3
    assert output[7] == expected_row
    assert all(output[r][c] == 2 for r in range(20) for c in range(22) if grid[r][c] == 2)
    assert output[1][5] == 0 and output[19][5] == 0
    assert grid == scene()


@pytest.mark.parametrize("setting", ["toward_trunk", "away_to_edge"])
def test_independent_renderer_is_covariant_under_transpose(setting):
    settings = {"branch_direction": setting}
    assert AUDIT.independent_apply(transpose(scene()), settings) == transpose(
        AUDIT.independent_apply(scene(), settings)
    )


@pytest.mark.parametrize("kind", ["bool_cell", "duplicate_alignment", "short_gap", "ragged"])
def test_independent_geometry_rejects_bad_grammar(kind):
    grid = scene()
    if kind == "bool_cell":
        grid[0][0] = False
    elif kind == "duplicate_alignment":
        grid[4][8] = 2
    elif kind == "short_gap":
        grid[7][8] = 0
        grid[7][6] = 2
    else:
        grid[-1].pop()
    with pytest.raises(ValueError):
        AUDIT.analyze_scene(grid)


@pytest.mark.parametrize("setting", ["toward_trunk", "away_to_edge"])
def test_two_core_orientations_refute_all_declared_rivals(setting):
    settings = {"branch_direction": setting}
    grids = [scene(), transpose(scene())]
    assert len(AUDIT.RIVALS) == 13
    for name in AUDIT.RIVALS:
        assert any(AUDIT.independent_apply(g, settings, name) !=
                   AUDIT.independent_apply(g, settings) for g in grids), name


def test_fitting_only_receives_demonstrations_and_freezes_survivors():
    grid = scene()
    demos = [{"input": grid, "output": grid}]
    calls = []
    def evaluate(program, value):
        calls.append((program, deepcopy(value)))
        return deepcopy(value) if program == "keep" else [[3] * len(value[0]) for _ in value]
    certificate = AUDIT.fit_demonstrations(demos, {"identity": "keep", "wrong": "paint"}, evaluate)
    assert certificate["survivors"] == ["identity"]
    assert certificate["demo_disagreements"] == {"identity": [], "wrong": [0]}
    assert len(calls) == 2
    assert all(value == grid for _, value in calls)
    assert certificate["query_accessed"] is False


@pytest.mark.parametrize("setting", ["toward_trunk", "away_to_edge"])
def test_protected_materialized_rivals_match_independent_renderer(setting):
    from arc_repl.racket_bridge import RacketBridge
    settings = {"branch_direction": setting}
    grids = [scene(), transpose(scene())]
    with RacketBridge(timeout=30, max_calls_before_restart=256) as bridge:
        executor = AUDIT.ProtectedExecutor(bridge)
        for name, program in AUDIT.rival_programs(settings).items():
            for grid in grids:
                assert executor.apply(program, grid) == AUDIT.independent_apply(grid, settings, name), name
        assert executor.evaluations

