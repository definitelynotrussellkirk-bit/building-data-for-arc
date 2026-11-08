"""Proposed height variant only; independent of canonical sampler repairs."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root


ROOT = find_root(__file__)
SOURCE = ROOT / "generators/c5dd8036311b/workspace/parametric/prototype.py"
SPEC = importlib.util.spec_from_file_location("c5dd_parametric_prototype", SOURCE)
P = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = P
SPEC.loader.exec_module(P)


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=10) as runtime:
        yield runtime


def mixed_grid():
    grid = [[0] * 7 for _ in range(9)]
    grid[6] = [8, 1, 1, 2, 1, 8, 1]
    return grid


@pytest.mark.parametrize("value", [True, False, 1, 6, -1, 3.0, "3", None])
def test_parameter_bounds_reject_noninteger_and_out_of_range_values(value):
    with pytest.raises(ValueError):
        P.Parameters(height_8=value)
    with pytest.raises(ValueError):
        P.Parameters(height_2=value)


def test_default_materialization_preserves_exact_canonical_program():
    assert P.racket_program(P.Parameters(), root=ROOT) == P.canonical_program(ROOT)
    assert len(P.all_parameters()) == 16


def test_default_racket_matches_all_original_pairs(bridge):
    program = P.racket_program(P.Parameters(), root=ROOT)
    pairs = canonical_pairs(P.TASK_ID, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert P.execute(bridge, program, pair["input"]) == pair["output"]


@pytest.mark.parametrize("heights", [(2, 5), (5, 2), (2, 2), (5, 5), (3, 4)])
def test_executed_heights_keep_tip_stem_bar_and_other_cells(bridge, heights):
    parameters = P.Parameters(*heights)
    grid = mixed_grid()
    original = deepcopy(grid)
    output = P.execute(bridge, P.racket_program(parameters, root=ROOT), grid)
    changed = set()
    for col, color in [(0, 8), (3, 2), (5, 8)]:
        height = parameters.height_8 if color == 8 else parameters.height_2
        assert [output[row][col] for row in range(6 - height, 6)] == [color] + [1] * (height - 1)
        changed.update((row, col) for row in range(6 - height, 6))
    assert grid == original
    assert len(output) == len(grid) and len(output[0]) == len(grid[0])
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if (row, col) not in changed:
                assert output[row][col] == grid[row][col]


def test_parameter_selection_and_inputs_are_episode_deterministic():
    assert P.choose_parameters(17) == P.choose_parameters(17)
    with pytest.raises(ValueError):
        P.choose_parameters(True)
    for index in range(4):
        first = P.build_input(17, index)
        assert first == P.build_input(17, index)
        assert first is not P.build_input(17, index)
        assert P.validate_input(first, P.Parameters(5, 5), require_both=True) == []
    assert len({P.grid_key(P.build_input(17, index)) for index in range(4)}) == 4


def test_every_setting_is_identifiable_under_every_query_holdout(bridge):
    programs = {p: P.racket_program(p, root=ROOT) for p in P.all_parameters()}
    inputs = [P.build_input(91, index) for index in range(4)]
    predictions = {p: [P.execute(bridge, program, grid) for grid in inputs]
                   for p, program in programs.items()}
    for parameters in P.all_parameters():
        pairs = [{"input": grid, "output": output} for grid, output in
                 zip(inputs, predictions[parameters], strict=True)]
        report = P.check_identifiability(pairs, parameters, predictions)
        assert report["identified_all_rotations"] is True
        assert len(report["rotations"]) == 4
        assert all(row["surviving_settings"] == [parameters.as_dict()]
                   for row in report["rotations"])


def test_missing_marker_demonstrations_expose_real_query_ambiguity(bridge):
    inputs = [P.build_input(51, i) for i in range(3)]
    for grid in inputs[:2]:
        for row in grid:
            for col, value in enumerate(row):
                if value == 8:
                    row[col] = 1
    predictions = {
        p: [P.execute(bridge, P.racket_program(p, root=ROOT), grid) for grid in inputs]
        for p in P.all_parameters()
    }
    chosen = P.Parameters()
    pairs = [{"input": grid, "output": output} for grid, output in
             zip(inputs, predictions[chosen], strict=True)]
    report = P.check_identifiability(pairs, chosen, predictions)
    last = report["rotations"][-1]
    assert len(last["surviving_settings"]) == 4
    assert len(last["query_ambiguities"]) == 3
    assert report["identified_all_rotations"] is False


def test_episode_uses_one_program_and_public_projection_hides_metadata(bridge):
    episode = P.make_episode(37, bridge=bridge, root=ROOT)
    chosen = P.Parameters(**episode["parameters"])
    program = P.racket_program(chosen, root=ROOT)
    for pair in episode["pairs"]:
        assert P.execute(bridge, program, pair["input"]) == pair["output"]
    public = P.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3 and len(public["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert set(public["test"][0]) == {"input"}
    public["train"][0]["input"][0][0] = 9
    assert episode["pairs"][0]["input"][0][0] == 0


def test_domain_checks_report_clipping_and_malformed_grids():
    grid = mixed_grid()
    assert P.validate_input(grid, P.Parameters(5, 5), require_both=True) == []
    clipped = [[0] * 7 for _ in range(6)]
    clipped[3] = [1, 8, 1, 2, 1, 1, 1]
    assert P.validate_input(clipped, P.Parameters(5, 5))
    for bad in ([], [[]], [[True]], [[10]], [[1, 8], [1]]):
        assert P.validate_input(bad, P.Parameters())
