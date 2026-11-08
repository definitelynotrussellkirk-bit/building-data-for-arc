"""Portable regressions for the frame-docking input sampler."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

TASK_ID = "43cca8eff94f"
HOME = Path(__file__).resolve().parents[1]
LIBRARY = next(
    (p for p in Path(__file__).resolve().parents if (p / "shared/runtime").is_dir()),
    None,
)
if LIBRARY is not None:
    sys.path.insert(0, str(LIBRARY / "shared/runtime"))
sys.path.insert(0, str(HOME / "workspace"))

from reviewer_support import canonical_pairs, find_root  # noqa: E402
from reference_probe import (  # noqa: E402
    CANONICAL_PROFILES,
    DIRECTION_SCHEDULE,
    analyze,
    load_generator,
    no_up_rival,
    slide_rule,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))


def labeled(grid):
    return {"input": deepcopy(grid), "output": slide_rule(grid)}


def test_metadata_pins_rule_and_exposes_only_exact_observable_axes():
    assert gen.GENERATOR_ID == gen.TASK_ID == TASK_ID
    assert gen.RULE_HASH == "ced1f6ce57f8"
    assert gen.VERSION == "3.0.0"
    assert gen.EXAMPLES_NEEDED == 4
    assert gen.LESSON_SCHEDULE_PERIOD == 5
    assert gen.MIN_STRICT_FRAC == 1.0
    assert set(gen.AXES) == {"grid_h", "grid_w", "direction", "obj_size", "gap"}
    assert tuple(gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS) == ()


@pytest.mark.parametrize("pair", PAIRS, ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_canonical_pairs_are_accepted_and_independent_oracle_matches(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert slide_rule(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {"grid_h": 9, "grid_w": 10, "direction": "up", "obj_size": 7, "gap": 3},
        {"grid_h": 18, "grid_w": 20, "direction": "right", "obj_size": 3, "gap": 1},
        {"grid_h": 10, "grid_w": 12, "direction": "left", "obj_size": 6, "gap": 2},
        {"grid_h": 11, "grid_w": 11, "direction": "down", "obj_size": 4, "gap": 3},
    ],
)
def test_exact_overrides_are_constructive_observable_and_band_independent(band, requested):
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid, difficulty=band, meta={"overrides": requested}) == []
    assert gen.observe_overrides(grid) == requested
    assert {name: analyze(grid)[name] for name in requested} == requested
    assert analyze(grid)["frame_is_hollow_rectangle"]
    assert slide_rule(grid) != grid


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"grid_h": 8}, {"grid_h": 19}, {"grid_h": True}, {"grid_h": 9.0},
        {"grid_w": 9}, {"grid_w": 21}, {"grid_w": "10"},
        {"direction": "diagonal"}, {"direction": 1},
        {"obj_size": 2}, {"obj_size": 8}, {"obj_size": False},
        {"gap": 0}, {"gap": 4}, {"gap": 2.0},
    ],
)
def test_invalid_and_unknown_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("difficulty", ["extreme", 0, 1, 0.0, 1.0, True])
def test_invalid_difficulty_scalars_fail_loudly(difficulty):
    with pytest.raises((TypeError, ValueError), match="difficulty"):
        gen.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize(
    "seed,sample_index",
    [(True, 0), (1.5, 0), (0, True), (0, False), (0, -1), (0, "2")],
)
def test_seed_and_sample_index_are_strict_scalars(seed, sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_five_sample_window_teaches_the_missing_up_branch(band):
    for start in range(10):
        grids = [gen.generate(700 + start, start + offset, difficulty=band) for offset in range(5)]
        directions = [analyze(grid)["direction"] for grid in grids]
        assert sorted(directions) == sorted(DIRECTION_SCHEDULE)
        assert any(analyze(grid)["profile"] in CANONICAL_PROFILES for grid in grids)
        pairs = [labeled(grid) for grid in grids]
        for held_out in range(5):
            demos = [pair for index, pair in enumerate(pairs) if index != held_out]
            query = pairs[held_out]
            if analyze(query["input"])["direction"] == "up":
                assert any(analyze(pair["input"])["direction"] == "up" for pair in demos)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_is_valid_diverse_and_covers_declared_axes(band):
    grids = [gen.generate(2100 + index, index, difficulty=band) for index in range(160)]
    signatures = set()
    directions, sizes, gaps, shapes = set(), set(), set(), set()
    for grid in grids:
        assert gen.self_check(grid) == []
        stats = analyze(grid)
        assert stats["frame_is_hollow_rectangle"]
        directions.add(stats["direction"])
        sizes.add(stats["obj_size"])
        gaps.add(stats["gap"])
        shapes.add((stats["grid_h"], stats["grid_w"]))
        signatures.add(json.dumps(grid, separators=(",", ":")))
    assert directions == {"right", "left", "down", "up"}
    assert sizes == set(range(3, 8))
    assert gaps == {1, 2, 3}
    assert len(shapes) >= 20
    assert len(signatures) >= 150


@pytest.mark.parametrize(
    "mutation",
    ["fill_frame", "break_frame", "disconnect_object", "add_object", "swap_colors", "bad_color", "ragged", "bool_cell"],
)
def test_self_check_rejects_destructive_mutations(mutation):
    grid = gen.generate(41, 4, grid_h=12, grid_w=14, direction="right", obj_size=5, gap=2)
    stats = analyze(grid)
    if mutation == "fill_frame":
        r1, c1, r2, c2 = stats["frame_box"]
        grid[(r1 + r2) // 2][(c1 + c2) // 2] = 8
    elif mutation == "break_frame":
        r, c = min(stats["frame_cells"])
        grid[r][c] = 0
    elif mutation == "disconnect_object":
        r, c = min(stats["object_cells"])
        grid[r][c] = 0
        for rr, row in enumerate(grid):
            for cc, value in enumerate(row):
                if value == 0 and all(abs(rr - r0) + abs(cc - c0) > 1 for r0, c0 in stats["object_cells"]):
                    grid[rr][cc] = 2
                    break
            else:
                continue
            break
    elif mutation == "add_object":
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value == 0 and all(abs(r - rr) + abs(c - cc) > 1 for rr, cc in stats["object_cells"]):
                    grid[r][c] = 2
                    break
            else:
                continue
            break
    elif mutation == "swap_colors":
        grid[:] = [[8 if v == 2 else 2 if v == 8 else v for v in row] for row in grid]
    elif mutation == "bad_color":
        grid[0][0] = 10
    elif mutation == "ragged":
        grid[0].pop()
    elif mutation == "bool_cell":
        grid[0][0] = True
    assert gen.self_check(grid)


def test_declared_up_witness_refutes_canonical_fitting_no_up_shortcut():
    assert all(no_up_rival(pair["input"]) == pair["output"] for pair in PAIRS)
    up_grid = gen.generate(91, 3)
    assert analyze(up_grid)["direction"] == "up"
    expected = slide_rule(up_grid)
    assert gen.SEMANTIC_WITNESSES["up_direction"](up_grid)
    assert gen.SEMANTIC_RIVALS["no_up"](up_grid) == no_up_rival(up_grid)
    assert gen.SEMANTIC_RIVALS["no_up"](up_grid) != expected
    assert gen.CANONICAL_SHORTCUTS["no_up"](up_grid) != expected


def test_generation_and_rivals_are_pure_deterministic_and_hashseed_independent():
    grid = gen.generate(8128, 23, difficulty="hard")
    assert grid == gen.generate(8128, 23, difficulty="hard")
    frozen = deepcopy(grid)
    for rival in gen.LESSON_COMPETITORS.values():
        rival(grid)
    assert grid == frozen

    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(subprocess.check_output(
            [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
            env=env, text=True,
        ))
    assert outputs[0] == outputs[1]
