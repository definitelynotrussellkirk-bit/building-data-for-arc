"""Focused native gravity contracts; Racket qualification checks actual labels."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root


TASK = "2a43e4f3a796"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK / "workspace/parametric"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


A = load(HOME / "adapter.py", "native_gravity_adapter_under_test")
G = load(HOME / "gravity.py", "native_gravity_core_under_test")
DIRECTIONS = ("down", "up", "left", "right")
SMALL = [[0, 5, 0, 2], [3, 0, 4, 0], [5, 1, 0, 2]]
EXPECTED = {
    "down": [[0, 0, 0, 0], [3, 5, 0, 2], [5, 1, 4, 2]],
    "up": [[3, 5, 4, 2], [5, 1, 0, 2], [0, 0, 0, 0]],
    "left": [[5, 2, 0, 0], [3, 4, 0, 0], [5, 1, 2, 0]],
    "right": [[0, 0, 5, 2], [0, 0, 3, 4], [0, 5, 1, 2]],
}


def assert_arc_grid(grid):
    assert type(grid) is list and 1 <= len(grid) <= 30
    assert type(grid[0]) is list and 1 <= len(grid[0]) <= 30
    assert all(type(row) is list and len(row) == len(grid[0]) for row in grid)
    assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)


def assert_stable_lines(before, after, direction):
    """Check observable conservation, ordering, and destination-edge packing."""
    assert_arc_grid(before)
    assert_arc_grid(after)
    assert (len(after), len(after[0])) == (len(before), len(before[0]))
    old_lines = list(zip(*before)) if direction in ("up", "down") else before
    new_lines = list(zip(*after)) if direction in ("up", "down") else after
    for old, new in zip(old_lines, new_lines):
        assert [v for v in new if v != 0] == [v for v in old if v != 0]
        occupied = [index for index, value in enumerate(new) if value != 0]
        if direction in ("down", "right"):
            assert occupied == list(range(len(new) - len(occupied), len(new)))
        else:
            assert occupied == list(range(len(occupied)))


@pytest.mark.parametrize("direction", DIRECTIONS)
def test_literal_direction_outputs_preserve_order_multiplicity_and_moving_gray(direction):
    original = deepcopy(SMALL)
    assert G.transform(original, direction) == EXPECTED[direction]
    assert original == SMALL


def test_default_is_down_and_zero_stays_background_when_gray_is_modal():
    grid = [[5, 5, 0], [5, 0, 5], [2, 5, 5]]
    assert G.transform(grid) == [[5, 0, 0], [5, 5, 5], [2, 5, 5]]


@pytest.mark.parametrize("grid", [
    [[0]], [[5]], [[0, 0, 0], [0, 0, 0]], [[5, 1], [2, 5]],
])
def test_blank_full_and_one_cell_inputs_are_lawful_fixed_points(grid):
    for direction in DIRECTIONS:
        assert G.transform(deepcopy(grid), direction) == grid


@pytest.mark.parametrize("direction", DIRECTIONS)
def test_single_row_and_column_keep_values_and_move_only_along_their_axis(direction):
    row = [[0, 5, 0, 2, 5, 0]]
    column = [[0], [5], [0], [2], [5], [0]]
    expected_row = {
        "down": row, "up": row,
        "left": [[5, 2, 5, 0, 0, 0]], "right": [[0, 0, 0, 5, 2, 5]],
    }
    expected_column = {
        "left": column, "right": column,
        "up": [[5], [2], [5], [0], [0], [0]],
        "down": [[0], [0], [0], [5], [2], [5]],
    }
    assert G.transform(row, direction) == expected_row[direction]
    assert G.transform(column, direction) == expected_column[direction]


def test_default_program_is_exact_selected_canonical_and_every_program_is_native():
    from puzzle_generators.rule_wrap import wrap_rule
    sources = {row["program_solution"] for line in canonical_path(ROOT).read_text().splitlines()
               if (row := json.loads(line)).get("task_id") == TASK}
    assert sources == {A.program({"gravity": "down"})}
    programs = [A.program({"gravity": direction}) for direction in DIRECTIONS]
    assert len(set(programs)) == 4
    assert all(wrap_rule(program).lstrip().startswith("(lambda") for program in programs)


def test_downward_transform_replays_every_canonical_pair():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert pairs
    for pair in pairs:
        assert G.transform(pair["input"], "down") == pair["output"]


@pytest.mark.parametrize("demos", range(2, 7))
def test_all_supported_demo_counts_supply_distinct_matched_inputs_and_stable_labels(demos):
    shared_inputs = None
    for direction in DIRECTIONS:
        settings = {"gravity": direction}
        episode = A.generate(0, settings, demos, 4)
        assert len(episode["train"]) == demos and len(episode["test"]) == 4
        assert episode["program_solution"] == A.program(settings)
        pairs = episode["train"] + episode["test"]
        inputs = [pair["input"] for pair in pairs]
        assert len({json.dumps(grid) for grid in inputs}) == demos + 4
        assert shared_inputs is None or inputs == shared_inputs
        shared_inputs = inputs
        for pair in pairs:
            assert_stable_lines(pair["input"], pair["output"], direction)
        shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
        assert shapes[0] == (30, 30)
        assert shapes[1] in ((19, 27), (27, 19))
        assert shapes[2:] == [(1, 30), (30, 1)]


def test_demo_and_query_counts_have_independent_stable_prefixes():
    settings = {"gravity": "left"}
    short = A.generate(17, settings, 2, 1)
    longer = A.generate(17, settings, 2, 4)
    more_demos = A.generate(17, settings, 6, 4)
    assert short["train"] == longer["train"] == more_demos["train"][:2]
    assert short["test"] == longer["test"][:1]
    assert longer["test"] == more_demos["test"]


def test_two_demo_prefix_separates_all_four_directions():
    for seed in (0, 17):
        demos = G.generate_inputs(seed, demos=2, queries=4)[:2]
        signatures = {json.dumps([G.transform(grid, direction) for grid in demos])
                      for direction in DIRECTIONS}
        assert len(signatures) == 4


def test_native_seed_upper_endpoint_is_deterministic_and_preserves_global_rng():
    state = random.getstate()
    settings = {"gravity": "up"}
    first = A.generate(2**63 - 1, settings, 2, 1)
    assert random.getstate() == state
    assert A.generate(2**63 - 1, settings, 2, 1) == first


@pytest.mark.parametrize("seed", [True, False, -1, 2**63, 0.0, "0", None])
def test_native_seed_types_and_bounds_fail_explicitly(seed):
    with pytest.raises((TypeError, ValueError)):
        A.generate(seed, {"gravity": "down"}, 2, 1)


@pytest.mark.parametrize("demos,queries", [
    (1, 4), (7, 4), (True, 4), (2.0, 4), ("2", 4),
    (3, 0), (3, 5), (3, True), (3, 1.0), (3, "1"),
])
def test_demo_query_counts_are_strict_and_never_clamped(demos, queries):
    with pytest.raises((TypeError, ValueError)):
        A.generate(0, {"gravity": "down"}, demos, queries)


@pytest.mark.parametrize("settings", [
    None, {}, "down", {"gravity": "diagonal"}, {"gravity": ""},
    {"gravity": True}, {"gravity": 0}, {"gravity": None}, {"gravity": ["down"]},
    {"gravity": "down", "extra": 0}, {"direction": "down"},
])
def test_settings_are_exact_and_never_silently_defaulted(settings):
    with pytest.raises((TypeError, ValueError)):
        A.program(settings)
    with pytest.raises((TypeError, ValueError)):
        A.generate(0, settings, 2, 1)


@pytest.mark.parametrize("grid", [
    [], [[]], [[0], [1, 2]], [[True]], [[1.0]], [[10]], [[-1]], [[0] * 31],
])
def test_malformed_grids_fail_before_transformation(grid):
    with pytest.raises((TypeError, ValueError)):
        G.transform(grid)
