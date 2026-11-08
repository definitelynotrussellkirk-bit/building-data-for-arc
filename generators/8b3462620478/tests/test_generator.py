"""Focused regressions for the reflected-beam generator repair."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import random
import sys

import pytest

TASK_ID = "8b3462620478"
TASK_DIR = Path(__file__).resolve().parents[1]
for candidate in (TASK_DIR, *TASK_DIR.parents):
    if (candidate / "shared/runtime/puzzle_generators/base.py").is_file():
        sys.path.insert(0, str(candidate / "shared/runtime"))
        break
    if (candidate / "puzzle_generators/base.py").is_file():
        sys.path.insert(0, str(candidate))
        break
else:
    raise RuntimeError("no independent puzzle_generators runtime found")

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", TASK_DIR / "generator.py"))
    spec = importlib.util.spec_from_file_location("generator_under_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
BANDS = (None, "easy", "medium", "hard")
DIRECTIONS = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1),
}


def canonical_labeled_pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def _reflect(direction, mirror):
    dr, dc = direction
    if mirror == 3:  # slash
        return -dc, -dr
    if mirror == 4:  # backslash
        return dc, dr
    return direction


def trace(grid, *, swap_mirrors=False, mirror_limit=None, repeat_first_turn=False):
    """Independent implementation of the pinned Racket rule plus rival knobs."""
    source = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    arrow = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
    if len(source) != 1 or len(arrow) != 1:
        raise ValueError("expected exactly one source and arrow")
    sr, sc = source[0]
    ar, ac = arrow[0]
    dr, dc = ar - sr, ac - sc
    if abs(dr) + abs(dc) != 1:
        return deepcopy(grid), {"mirrors": (), "turn_sides": (), "stop": "bad_heading"}

    h, w = len(grid), len(grid[0])
    out = deepcopy(grid)
    r, c = ar + dr, ac + dc
    mirrors = []
    turn_sides = []
    first_side = None
    for _fuel in range(500):
        if not (0 <= r < h and 0 <= c < w):
            return out, {"mirrors": tuple(mirrors), "turn_sides": tuple(turn_sides), "stop": "edge"}
        value = grid[r][c]
        if value == 5:
            return out, {"mirrors": tuple(mirrors), "turn_sides": tuple(turn_sides), "stop": "wall"}
        if value == 0:
            out[r][c] = 8
        if value in (3, 4):
            mirrors.append((r, c, value))
            before = (dr, dc)
            if mirror_limit is None or len(mirrors) <= mirror_limit:
                if repeat_first_turn and first_side is not None:
                    right = (before[1], -before[0])
                    after = right if first_side == "right" else (-right[0], -right[1])
                else:
                    use = 7 - value if swap_mirrors else value
                    after = _reflect(before, use)
                right = (before[1], -before[0])
                side = "right" if after == right else "left"
                if first_side is None:
                    first_side = side
                dr, dc = after
                turn_sides.append(side)
        r, c = r + dr, c + dc
    return out, {"mirrors": tuple(mirrors), "turn_sides": tuple(turn_sides), "stop": "fuel"}


def observed(grid):
    source = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2)
    arrow = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1)
    delta = arrow[0] - source[0], arrow[1] - source[1]
    direction = {value: key for key, value in DIRECTIONS.items()}[delta]
    _, report = trace(grid)
    first = report["mirrors"][0][2]
    after = _reflect(delta, first)
    right = (delta[1], -delta[0])
    turn_side = "right" if after == right else "left"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_mirrors": sum(value in (3, 4) for row in grid for value in row),
        "n_walls": sum(
            grid[r][c] == 5
            for r in range(1, len(grid) - 1)
            for c in range(1, len(grid[0]) - 1)
        ),
        "direction": direction,
        "turn_side": turn_side,
    }


def test_rule_pin_canonical_acceptance_and_independent_outputs():
    assert gen.RULE_HASH == "805506f84e33"
    pairs = canonical_labeled_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert trace(pair["input"])[0] == pair["output"]
        assert pair["input"] == original


def test_first_three_mirror_shortcut_fits_canonical_but_has_generated_witness():
    assert set(gen.CANONICAL_SHORTCUTS) == {"first_three_mirrors_only"}
    rival = gen.CANONICAL_SHORTCUTS["first_three_mirrors_only"]
    assert all(rival(pair["input"]) == pair["output"] for pair in canonical_labeled_pairs())

    grid = gen.generate(31415, 2, n_mirrors=4, n_walls=1, direction="down")
    truth, report = trace(grid)
    assert len(report["mirrors"]) == 4
    assert rival(grid) != truth


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("direction", tuple(DIRECTIONS))
@pytest.mark.parametrize("turn_side", ("left", "right"))
def test_minimum_exact_overrides_are_visible_and_interactive(band, direction, turn_side):
    requested = {
        "grid_h": 9,
        "grid_w": 12,
        "n_mirrors": 2,
        "n_walls": 0,
        "direction": direction,
        "turn_side": turn_side,
    }
    grid = gen.generate(1701, 22, difficulty=band, **requested)
    assert gen.self_check(grid, difficulty=band) == []
    assert gen.strict_canonical_like(grid) == []
    assert observed(grid) == requested
    assert gen.observe_overrides(grid) == requested
    output, report = trace(grid)
    assert len(report["mirrors"]) == 2
    assert {item[2] for item in report["mirrors"]} == {3, 4}
    assert report["stop"] == "wall"
    assert all(value == 5 for value in grid[0] + grid[-1])
    assert all(row[0] == 5 and row[-1] == 5 for row in grid)
    assert output == gen._intended_output(grid)


@pytest.mark.parametrize("band", BANDS)
def test_maximum_exact_overrides_hit_every_mirror_and_stop_at_wall(band):
    requested = {
        "grid_h": 18,
        "grid_w": 20,
        "n_mirrors": 6,
        "n_walls": 6,
        "direction": "right",
        "turn_side": "right",
    }
    grid = gen.generate(901, 7, difficulty=band, **requested)
    assert gen.self_check(grid, difficulty=band) == []
    assert observed(grid) == requested
    output, report = trace(grid)
    assert output == gen._intended_output(grid)
    assert report["stop"] == "wall"
    assert all(value == 5 for value in grid[0] + grid[-1])
    assert all(row[0] == 5 and row[-1] == 5 for row in grid)
    assert len(report["mirrors"]) == 6
    assert set(report["turn_sides"]) == {"left", "right"}


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_default_distribution_is_deterministic_and_covers_rule_axes(band):
    random.seed(9917)
    state = random.getstate()
    grids = [gen.generate(5000 + i, i * 7, difficulty=band) for i in range(160)]
    assert random.getstate() == state
    assert all(gen.self_check(grid, difficulty=band) == [] for grid in grids)
    assert all(grid == gen.generate(5000 + i, i * 7, difficulty=band) for i, grid in enumerate(grids))
    stats = [observed(grid) for grid in grids]
    assert {item["direction"] for item in stats} == set(DIRECTIONS)
    assert {item["turn_side"] for item in stats} == {"left", "right"}
    assert {item["n_mirrors"] for item in stats} == set(range(2, 7))
    assert {item["n_walls"] for item in stats} == set(range(0, 7))
    canonical_profiles = {
        (10, 12, 5),
        (11, 13, 6),
        (10, 14, 6),
        (11, 12, 6),
        (10, 13, 6),
    }
    first_twenty_profiles = {
        (len(grid), len(grid[0]), len({value for row in grid for value in row}))
        for grid in grids[:20]
    }
    assert first_twenty_profiles & canonical_profiles
    canonical_envelope = [
        grid for grid in grids
        if 10 <= len(grid) <= 11
        and 12 <= len(grid[0]) <= 14
        and 5 <= len({value for row in grid for value in row}) <= 6
    ]
    assert len(canonical_envelope) >= 100
    assert all(all(value == 5 for value in grid[0] + grid[-1]) for grid in grids)
    assert all(all(row[0] == 5 and row[-1] == 5 for row in grid) for grid in grids)


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_every_generated_route_uses_all_mirrors_and_refutes_declared_rivals(band):
    for index in range(40):
        grid = gen.generate(7300 + index, index, difficulty=band)
        truth, report = trace(grid)
        assert gen._intended_output(grid) == truth
        assert len(report["mirrors"]) == observed(grid)["n_mirrors"]
        mirrors = observed(grid)["n_mirrors"]
        minimum_witness_size = {
            "first_two_mirrors_only": 3,
            "first_three_mirrors_only": 4,
            "repeat_first_turn_side": 3,
        }
        for name, rival in gen.SEMANTIC_RIVALS.items():
            if mirrors >= minimum_witness_size.get(name, 0):
                assert rival(deepcopy(grid)) != truth, name


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_every_three_demo_window_refutes_all_declared_competitors(band):
    assert gen.EXAMPLES_NEEDED == 3
    for start in range(12):
        demos = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(8800 + start, sample_index, difficulty=band)
            demos.append({"input": grid, "output": trace(grid)[0]})
        query_grid = gen.generate(8800 + start, start + gen.EXAMPLES_NEEDED, difficulty=band)
        query = {"input": query_grid, "output": trace(query_grid)[0]}
        assert gen.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"texture": "default"},
        {"grid_h": 8},
        {"grid_h": 19},
        {"grid_w": 11},
        {"grid_w": 21},
        {"n_mirrors": 1},
        {"n_mirrors": 7},
        {"n_walls": -1},
        {"n_walls": 7},
        {"direction": "diagonal"},
        {"turn_side": "center"},
        {"grid_h": True},
        {"n_mirrors": 2.0},
        {"n_walls": "2"},
    ],
)
def test_invalid_overrides_fail_closed(overrides):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("difficulty", ("trivial", 0.5, True))
def test_invalid_difficulty_fails_closed(difficulty):
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 0]],
        [[True, 0], [0, 1]],
        [[10, 0], [0, 1]],
        [[2, 1]],
        [[2, 0], [0, 1]],
    ],
)
def test_malformed_or_semantically_empty_grids_are_diagnostic_not_exceptions(grid):
    assert gen.self_check(grid)


def test_workspace_probe_replays_saved_first_three_mirror_counterexample():
    probe_path = TASK_DIR / "workspace" / "reference_probe.py"
    spec = importlib.util.spec_from_file_location("reference_probe", probe_path)
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    record = json.loads(
        (TASK_DIR / "counterexamples" / "first_three_mirrors_only.json").read_text()
    )
    truth, report = probe.trace(record["input"])
    rival, rival_report = probe.trace(record["input"], mirror_limit=3)
    assert truth == record["intended_output"]
    assert rival == record["rival_output"]
    assert truth != rival
    assert len(report["mirrors"]) == 4
    assert len(rival_report["mirrors"]) == 4
    assert report["stop"] == "wall"
