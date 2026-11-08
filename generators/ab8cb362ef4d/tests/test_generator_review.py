"""Task-local regression and semantic-contract tests for ab8cb362ef4d."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (canonical_pairs, first_frame_only, gravity_output,
                             load_generator, observed, one_per_column,
                             preserve_damaged_border)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))

EXPECTED_AXES = {
    "grid_h": {"type": "int", "valid": "11..16"},
    "grid_w": {"type": "int", "valid": "12..18"},
    "n_frames": {"type": "int", "valid": "1..3"},
    "n_colors": {"type": "int", "valid": "2..7"},
    "column_pattern": {"type": "str", "valid": "separate|stacked|mixed"},
    "border_overwrites": {"type": "int", "valid": "0..1"},
}


def test_authority_pin_and_honest_axis_surface():
    assert gen.RULE_HASH == "94102b577ef7"
    assert set(gen.AXES) == set(EXPECTED_AXES)
    for name, spec in EXPECTED_AXES.items():
        assert gen.AXES[name]["type"] == spec["type"]
        assert gen.AXES[name]["valid"] == spec["valid"]
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.DEGENERATE_TEXTURES == ()
    assert gen.HELPFUL_TEXTURES == ()


@pytest.mark.parametrize("pair", canonical_pairs(), ids=lambda p: f"{len(p['input'])}x{len(p['input'][0])}")
def test_accepts_every_canonical_input_and_matches_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert gravity_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("n_frames", [1, 2, 3])
@pytest.mark.parametrize("n_colors", [2, 7])
@pytest.mark.parametrize("column_pattern", ["separate", "stacked", "mixed"])
@pytest.mark.parametrize("border_overwrites", [0, 1])
def test_boundary_exact_overrides_are_constructive_and_pixel_observable(
        band, n_frames, n_colors, column_pattern, border_overwrites):
    options = {
        "grid_h": 11,
        "grid_w": 12,
        "n_frames": n_frames,
        "n_colors": n_colors,
        "column_pattern": column_pattern,
        "border_overwrites": border_overwrites,
    }
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert gravity_output(grid) != grid


@pytest.mark.parametrize("key,value", [
    ("typo", 1), ("grid_h", 10), ("grid_h", 17), ("grid_h", True),
    ("grid_w", 11), ("grid_w", 19), ("n_frames", 0), ("n_frames", 4),
    ("n_colors", 1), ("n_colors", 8), ("n_colors", 2.0),
    ("column_pattern", "columns"), ("column_pattern", 1),
    ("border_overwrites", -1), ("border_overwrites", 2),
])
def test_invalid_overrides_fail_loudly(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_schedule_is_deterministic_profile_supported_and_semantically_rich(band):
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]),
         len({v for row in pair["input"] for v in row}))
        for pair in canonical_pairs()
    }
    exact = 0
    schedules = set()
    for index in range(60):
        grid = gen.generate(600 + index, index, difficulty=band)
        assert grid == gen.generate(600 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        stats = observed(grid)
        schedules.add((stats["n_frames"], stats["column_pattern"], stats["border_overwrites"]))
        profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
        exact += profile in canonical_profiles
    assert exact >= 30
    assert {(2, "mixed", 1), (3, "separate", 0), (1, "stacked", 0)} <= schedules


def test_every_three_consecutive_examples_refute_all_declared_competitors():
    for band in ("easy", "medium", "hard"):
        for start in range(24):
            demos = []
            for offset in range(3):
                grid = gen.generate(1009 + start, start + offset, difficulty=band)
                demos.append({"input": grid, "output": gravity_output(grid)})
            query_grid = gen.generate(1009 + start, start + 3, difficulty=band)
            query = {"input": query_grid, "output": gravity_output(query_grid)}
            assert gen.lesson_identifiable(demos, query) == []
            for rival in gen.LESSON_COMPETITORS.values():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos)


def test_named_witnesses_are_real_counterexamples_to_their_named_rivals():
    grids = {
        "multiple_frames": gen.generate(8, 0, n_frames=3, column_pattern="separate", border_overwrites=0),
        "damaged_border": gen.generate(8, 1, n_frames=2, column_pattern="mixed", border_overwrites=1),
        "stacked_column": gen.generate(8, 2, n_frames=1, column_pattern="stacked", border_overwrites=0),
    }
    intended = {name: gravity_output(grid) for name, grid in grids.items()}
    for witness, grid in grids.items():
        assert gen.SEMANTIC_WITNESSES[witness](grid)
        for rival_name in gen.WITNESS_RIVALS[witness]:
            assert gen.SEMANTIC_RIVALS[rival_name](grid) != intended[witness]
    assert gen.SEMANTIC_RIVALS["first_frame_only"](grids["multiple_frames"]) == first_frame_only(grids["multiple_frames"])
    assert gen.SEMANTIC_RIVALS["preserve_damaged_border"](grids["damaged_border"]) == preserve_damaged_border(grids["damaged_border"])
    assert gen.SEMANTIC_RIVALS["one_per_column"](grids["stacked_column"]) == one_per_column(grids["stacked_column"])


@pytest.mark.parametrize("mutation", [
    "zero_border_gap", "interior_five", "outside_marker", "erase_all_fives", "identity_only",
])
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(31, 4, grid_h=13, grid_w=15, n_frames=2, n_colors=6,
                        column_pattern="mixed", border_overwrites=1)
    boxes = gen._frame_boxes(grid)
    r0, c0, r1, c1 = boxes[0]
    if mutation == "zero_border_gap":
        grid[r0][c0 + 1] = 0
    elif mutation == "interior_five":
        grid[r0 + 1][c0 + 1] = 5
    elif mutation == "outside_marker":
        occupied = {(r, c) for a, b, x, y in boxes for r in range(a, x + 1) for c in range(b, y + 1)}
        r, c = next((r, c) for r in range(len(grid)) for c in range(len(grid[0])) if (r, c) not in occupied)
        grid[r][c] = 2
    elif mutation == "erase_all_fives":
        for row in grid:
            for c, value in enumerate(row):
                if value == 5:
                    row[c] = 0
    elif mutation == "identity_only":
        for a, b, x, y in boxes:
            for r in range(a + 1, x):
                for c in range(b + 1, y):
                    if grid[r][c] not in (0, 5):
                        grid[r][c] = 0
            grid[x - 1][b + 1] = 2
            grid[x - 1][b + 2] = 3
    assert gen.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 12 for _ in range(11)]])
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_oracles_do_not_mutate_inputs():
    grid = gen.generate(71, 5, n_frames=3, column_pattern="mixed", border_overwrites=1)
    before = deepcopy(grid)
    gravity_output(grid)
    for rival in gen.SEMANTIC_RIVALS.values():
        rival(grid)
    assert grid == before


def test_generation_is_python_hash_seed_independent():
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


def test_real_racket_reference_when_available():
    from arc_repl.racket_bridge import racket_runtime_status
    from reference_probe import racket_outputs
    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(319, i, difficulty=("easy", "medium", "hard")[i % 3]) for i in range(36)]
    assert racket_outputs(grids) == [gravity_output(grid) for grid in grids]
