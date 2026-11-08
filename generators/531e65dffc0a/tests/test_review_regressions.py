"""Black-box regressions for anchor-coded rotation stamps.

Run in a library with ``PYTHONPATH=shared/runtime python -m pytest -q
generators/531e65dffc0a/tests/test_review_regressions.py``. The same file
works under ``tests/531e65dffc0a`` in a copied portable runtime. Public
canonical pairs are authoring evidence; do not open them during blind solves.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import random
import sys

import pytest


# Bootstrap only from the tree containing this test, independent of shell cwd.
for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import canonical_pairs, find_root  # noqa: E402


TASK_ID = "531e65dffc0a"
ROOT = find_root(__file__)
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
if not GENERATOR_PATH.is_file():
    GENERATOR_PATH = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"review_regressions_{TASK_ID}", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gen
SPEC.loader.exec_module(gen)
PAIRS = canonical_pairs(TASK_ID, root=ROOT)
ANCHOR_CODES = {2, 3, 4, 5}


def observe(grid):
    """Recover exact controls directly from pixels, not generator metadata."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "proto_size": sum(v not in ({0} | ANCHOR_CODES) for row in grid for v in row),
        "n_anchors": sum(v in ANCHOR_CODES for row in grid for v in row),
    }


def assert_scene(grid):
    assert isinstance(grid, list) and grid and grid[0]
    width = len(grid[0])
    assert all(isinstance(row, list) and len(row) == width for row in grid)
    assert all(type(v) is int and 0 <= v <= 9 for row in grid for v in row)
    prototype = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
                 if v not in ({0} | ANCHOR_CODES)}
    anchors = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
               if v in ANCHOR_CODES}
    assert prototype and anchors
    assert len({grid[r][c] for r, c in prototype}) == 1
    frontier = [next(iter(prototype))]
    reached = set(frontier)
    while frontier:
        r, c = frontier.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            neighbor = (r + dr, c + dc)
            if neighbor in prototype and neighbor not in reached:
                reached.add(neighbor)
                frontier.append(neighbor)
    assert reached == prototype, "the prototype must be one 4-connected shape"
    for r, c in anchors:
        assert all((r + dr, c + dc) not in (prototype | anchors)
                   for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))
    assert gen.self_check(grid) == []


@pytest.mark.parametrize("pair", PAIRS, ids=[
    f"variant{p['variant']}-{p['split']}{p['pair_index']}" for p in PAIRS
])
def test_all_canonical_inputs_are_accepted_without_mutation(pair):
    grid = deepcopy(pair["input"])
    assert_scene(grid)
    assert grid == pair["input"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("controls", [
    {"grid_h": 8}, {"grid_h": 16},
    {"grid_w": 8}, {"grid_w": 16},
    {"proto_size": 2}, {"proto_size": 6},
    {"n_anchors": 1}, {"n_anchors": 6},
    {"grid_h": 8, "grid_w": 8, "proto_size": 6, "n_anchors": 6},
    {"grid_h": 16, "grid_w": 16, "proto_size": 2, "n_anchors": 1},
])
def test_declared_controls_are_realized_in_every_difficulty(controls, difficulty):
    grid = gen.generate(17, 29, difficulty=difficulty, **controls)
    assert_scene(grid)
    realized = observe(grid)
    for key, expected in controls.items():
        assert realized[key] == expected, (key, controls, realized)


@pytest.mark.parametrize("controls", [
    {"__override_contract_unknown_axis__": 1},
    {"difficulty": "expert"},
    {"grid_h": "8"}, {"grid_w": 8.0},
    {"proto_size": True}, {"n_anchors": False},
    {"grid_h": 7}, {"grid_w": 7},
    {"proto_size": 1}, {"proto_size": 7},
    {"n_anchors": 0}, {"n_anchors": 7},
    {"proto_color": 0}, {"proto_color": 2}, {"proto_color": 10},
    {"proto_color": True}, {"proto_color": "6"}, {"proto_color": 6.0},
])
def test_invalid_and_unknown_controls_reject_loudly(controls):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(17, 29, **controls)


@pytest.mark.parametrize("color", [1, 6, 7, 8, 9])
@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_prototype_color_override_is_observed_exactly(color, difficulty):
    grid = gen.generate(117, 29, difficulty=difficulty, proto_color=color)
    assert_scene(grid)
    observed = {v for row in grid for v in row if v not in ({0} | ANCHOR_CODES)}
    assert observed == {color}


def valid_scene():
    grid = [[0] * 10 for _ in range(10)]
    grid[0][0] = grid[1][0] = grid[1][1] = 6
    grid[4][5] = 3
    return grid


def corrupt_scene(kind):
    grid = valid_scene()
    if kind == "no_prototype":
        for r, c in ((0, 0), (1, 0), (1, 1)):
            grid[r][c] = 0
    elif kind == "no_anchor":
        grid[4][5] = 0
    elif kind == "disconnected_prototype":
        grid[8][8] = 6
    elif kind == "multiple_prototype_colors":
        grid[1][1] = 7
    elif kind == "anchor_touching_prototype":
        grid[2][1] = 2
    elif kind == "touching_anchors":
        grid[4][6] = 2
    elif kind == "out_of_palette":
        grid[1][1] = 10
    elif kind == "non_integer_color":
        grid[1][1] = 6.0
    elif kind == "boolean_color":
        grid[1][1] = True
    elif kind == "ragged":
        grid[-1].pop()
    else:
        raise AssertionError(kind)
    return grid


@pytest.mark.parametrize("kind", [
    "no_prototype", "no_anchor", "disconnected_prototype",
    "multiple_prototype_colors", "anchor_touching_prototype", "touching_anchors",
    "out_of_palette", "non_integer_color", "boolean_color", "ragged",
])
def test_self_check_rejects_structural_impostors_without_mutation(kind):
    grid = corrupt_scene(kind)
    before = deepcopy(grid)
    errors = gen.self_check(grid)
    assert isinstance(errors, list) and errors, kind
    assert all(isinstance(error, str) and error for error in errors)
    assert grid == before


def test_self_check_does_not_overfit_generated_shape_or_position():
    # Neither connected four-cell shape has the top-left bbox cell occupied.
    # Such an origin is lawful and occurs in the public test input.
    for cells in (((0, 1), (1, 0), (1, 1), (1, 2)),
                  ((0, 1), (0, 2), (1, 0), (1, 1))):
        grid = [[0] * 10 for _ in range(10)]
        for r, c in cells:
            grid[r + 2][c + 3] = 9
        grid[7][1] = 4
        assert_scene(grid)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_small_canvas_never_silently_sheds_requested_anchors(difficulty):
    for seed in range(24):
        controls = {"grid_h": 8, "grid_w": 8, "proto_size": 6, "n_anchors": 6}
        grid = gen.generate(seed, seed * 17 + 1, difficulty=difficulty, **controls)
        assert_scene(grid)
        assert observe(grid) == controls


def test_deterministic_fresh_returns_and_global_rng_isolation():
    random.seed(9811)
    before = random.getstate()
    first = gen.generate(91, 117, difficulty="hard")
    assert random.getstate() == before
    second = gen.generate(91, 117, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
