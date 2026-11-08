"""Independent, bounded checks of the row-run parametric teaching contract.

The explicit expected grids below are hand-derived.  The wrong-rule audit
segments independently with itertools.groupby and does not use prototype
segmentation, traversal, or teaching-report helpers.  Real protected Racket
execution checks both those fixtures and the sampled generated episodes.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from itertools import groupby
from pathlib import Path
import sys

import pytest


TASK_DIR = Path(__file__).resolve().parents[1]
REPO = TASK_DIR.parents[1]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load_local(filename):
    path = TASK_DIR / "workspace" / "parametric" / filename
    name = "_be5d9fa6fec1_adversarial_" + path.stem
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prototype = _load_local("prototype.py")
adapter = _load_local("adapter.py")
MODES = ("fixed3", "height_plus_one")


# Maximal run heights [2,1,1,3,1,1,1,1].  After selecting run 3,
# the adaptive traversal must read height 3 and land on run 7, not run 6.
RECURRENCE_INPUT = [
    [1, 0, 1], [1, 0, 1], [0, 1, 1], [1, 0, 1],
    [8, 8, 0], [8, 8, 0], [8, 8, 0], [0, 8, 8],
    [1, 1, 0], [8, 0, 8], [0, 1, 0],
]
RECURRENCE_OUTPUTS = {
    "fixed3": [
        [2, 0, 2], [2, 0, 2], [0, 1, 1], [1, 0, 1],
        [2, 2, 0], [2, 2, 0], [2, 2, 0], [0, 8, 8],
        [1, 1, 0], [2, 0, 2], [0, 1, 0],
    ],
    "height_plus_one": [
        [2, 0, 2], [2, 0, 2], [0, 1, 1], [1, 0, 1],
        [2, 2, 0], [2, 2, 0], [2, 2, 0], [0, 8, 8],
        [1, 1, 0], [8, 0, 8], [0, 2, 0],
    ],
}

# Run heights [1,2,3,1,2,1,1,1].  Adaptive targets 0,2,6;
# the first run's height alone would instead give targets 0,2,4,6.
SECOND_HEIGHT_INPUT = [
    [1, 0, 1], [0, 1, 1], [0, 1, 1], [1, 0, 1],
    [1, 0, 1], [1, 0, 1], [8, 8, 0], [0, 8, 8],
    [0, 8, 8], [1, 1, 0], [8, 0, 8], [0, 1, 0],
]
SECOND_HEIGHT_OUTPUTS = {
    "fixed3": [
        [2, 0, 2], [0, 1, 1], [0, 1, 1], [1, 0, 1],
        [1, 0, 1], [1, 0, 1], [2, 2, 0], [0, 8, 8],
        [0, 8, 8], [1, 1, 0], [2, 0, 2], [0, 1, 0],
    ],
    "height_plus_one": [
        [2, 0, 2], [0, 1, 1], [0, 1, 1], [2, 0, 2],
        [2, 0, 2], [2, 0, 2], [8, 8, 0], [0, 8, 8],
        [0, 8, 8], [1, 1, 0], [2, 0, 2], [0, 1, 0],
    ],
}

# Runs 0,1,2 have the same foreground color but different full rows.
# Pattern A occurs at runs 0,2,5; the last occurrence must remain unchanged.
EXACT_ROW_INPUT = [
    [1, 0, 1], [0, 1, 1], [1, 0, 1], [1, 1, 1],
    [1, 1, 1], [8, 0, 8], [1, 0, 1],
]
EXACT_ROW_OUTPUTS = {
    "fixed3": [
        [2, 0, 2], [0, 1, 1], [1, 0, 1], [2, 2, 2],
        [2, 2, 2], [8, 0, 8], [1, 0, 1],
    ],
    "height_plus_one": [
        [2, 0, 2], [0, 1, 1], [2, 0, 2], [1, 1, 1],
        [1, 1, 1], [2, 0, 2], [1, 0, 1],
    ],
}
FIXTURES = (
    ("newly_reached_run_height", RECURRENCE_INPUT, RECURRENCE_OUTPUTS),
    ("height_changes_twice", SECOND_HEIGHT_INPUT, SECOND_HEIGHT_OUTPUTS),
    ("full_rows_and_repeated_patterns", EXACT_ROW_INPUT, EXACT_ROW_OUTPUTS),
)


@pytest.fixture(scope="module")
def racket_apply():
    from puzzle_generators import runner

    bridge, first_name = runner._open_bridge_with_rule(
        runner.wrap_rule(adapter.program({"step_mode": "fixed3"}))
    )
    try:
        identity = bridge.runtime_identity
        assert identity["backend"] == "racket"
        assert identity["protected"] is True
        second_name = "__be5d9_adversarial_height"
        bridge.eval_text(
            f"(define {second_name} "
            + runner.wrap_rule(adapter.program({"step_mode": "height_plus_one"}))
            + ")"
        )
        names = {"fixed3": first_name, "height_plus_one": second_name}

        def apply(grid, mode):
            return runner._apply_rule(bridge, names[mode], deepcopy(grid))

        yield apply
    finally:
        bridge.close()


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("_name,grid,outputs", FIXTURES, ids=[row[0] for row in FIXTURES])
def test_hand_derived_segmentation_and_recurrence(_name, grid, outputs, mode, racket_apply):
    original = deepcopy(grid)
    settings = {"step_mode": mode}
    assert prototype.solve(grid, settings) == outputs[mode]
    assert racket_apply(grid, mode) == outputs[mode]
    assert grid == original


def _group_positions(grid, key=tuple):
    """Physical row positions grouped independently of prototype code."""
    return [
        [index for index, _row in chunk]
        for _value, chunk in groupby(enumerate(grid), key=lambda item: key(item[1]))
    ]


def _paint_positions(grid, positions):
    chosen = set(positions)
    return [
        [2 if index in chosen and value != 0 else value for value in row]
        for index, row in enumerate(grid)
    ]


def _rival_prediction(grid, mode, rival):
    groups = _group_positions(grid)
    if rival == "foreground_kind_groups":
        groups = _group_positions(grid, lambda row: tuple(sorted(set(row) - {0})))
    elif rival == "global_unique_patterns":
        buckets = {}
        for index, row in enumerate(grid):
            buckets.setdefault(tuple(row), []).append(index)
        groups = list(buckets.values())

    if rival.startswith("fixed_stride_"):
        stride = int(rival.rsplit("_", 1)[1])
    elif rival == "first_height_forever":
        stride = len(groups[0]) + 1
    else:
        stride = None

    positions = []
    cursor = 0
    while cursor < len(groups):
        positions.extend(groups[cursor])
        cursor += stride if stride is not None else (
            3 if mode == "fixed3" else len(groups[cursor]) + 1
        )
    return _paint_positions(grid, positions)


@pytest.mark.parametrize("mode", MODES)
def test_literal_fixtures_are_nonvacuous_against_both_extra_risks(mode):
    for rival in ("first_height_forever", "foreground_kind_groups", "global_unique_patterns"):
        assert any(
            _rival_prediction(grid, mode, rival) != outputs[mode]
            for _name, grid, outputs in FIXTURES
        ), rival


@pytest.mark.parametrize("seed", [0, 17])
@pytest.mark.parametrize("mode", MODES)
def test_two_visible_demos_refute_independent_rivals_for_four_queries(seed, mode, racket_apply):
    settings = {"step_mode": mode}
    episode = adapter.generate(seed, settings, demos=2, queries=4)
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 4
    pairs = episode["train"] + episode["test"]
    assert len({tuple(map(tuple, pair["input"])) for pair in pairs}) == 6
    assert episode["program_solution"] == adapter.program(settings)

    for pair in pairs:
        assert racket_apply(pair["input"], mode) == pair["output"]

    rivals = [
        "fixed_stride_2", "fixed_stride_4", "first_height_forever",
        "foreground_kind_groups", "global_unique_patterns",
    ]
    if mode == "height_plus_one":
        rivals.append("fixed_stride_3")
    for rival in rivals:
        # Query answers never contribute to eliminating a wrong rule.
        fits_visible_demos = all(
            _rival_prediction(pair["input"], mode, rival) == pair["output"]
            for pair in episode["train"]
        )
        assert not fits_visible_demos, (seed, mode, rival)

