"""Source-bound regression tests for b9d1d323c3ed."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import random
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (
    analyze,
    canonical_pairs,
    canonical_row,
    fixed_3x3_rival,
    intended_output,
    load_generator,
    normalized_rule_hash,
    racket_outputs,
    witness_input,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
BANDS = (None, "easy", "medium", "hard")


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "train2", "test0"])
def test_canonical_pairs_are_owned_and_match_independent_oracle(pair):
    assert gen.self_check(deepcopy(pair["input"])) == []
    assert intended_output(pair["input"]) == pair["output"]


def test_rule_hash_pins_selected_canonical_source():
    assert gen.RULE_HASH == normalized_rule_hash(canonical_row()["program_solution"])


@pytest.mark.parametrize("band", BANDS)
def test_exact_observable_overrides_work_in_every_band(band):
    options = {
        "grid_h": 8,
        "grid_w": 8,
        "fg_color": 9,
        "bbox_size_kind": "small",
        "bbox_position_bias": "center",
        "fg_layout": "diagonal",
    }
    grid = gen.generate(17, 5, difficulty=band, **options)
    info = analyze(grid)
    assert gen.self_check(grid) == []
    assert (info["grid_h"], info["grid_w"], info["fg_color"]) == (8, 8, 9)
    assert (info["bbox_h"], info["bbox_w"]) == (2, 2)
    assert info["bbox"] == (3, 4, 3, 4)
    assert info["crop"] == [[9, 0], [0, 9]]
    assert gen.observe_overrides(grid) == {"grid_h": 8, "grid_w": 8, "fg_color": 9}


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 7),
        ("grid_h", 19),
        ("grid_w", True),
        ("grid_w", 8.0),
        ("fg_color", 0),
        ("fg_color", "4"),
        ("bbox_size_kind", "huge"),
        ("bbox_position_bias", "random"),
        ("fg_layout", "solid"),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(3, 2, **{key: value})


@pytest.mark.parametrize("band", BANDS)
def test_default_distribution_is_deterministic_lawful_and_disambiguating(band):
    grid_shapes: set[tuple[int, int]] = set()
    bbox_shapes: set[tuple[int, int]] = set()
    colors: set[int] = set()
    variable = core = 0
    for index in range(128):
        seed = 1000 + index
        before = random.getstate()
        grid = gen.generate(seed, index, difficulty=band)
        assert random.getstate() == before
        assert grid == gen.generate(seed, index, difficulty=band)
        assert gen.self_check(deepcopy(grid)) == []
        info = analyze(grid)
        output = intended_output(grid)
        assert len(output) < len(grid)
        assert len(output[0]) < len(grid[0])
        assert len({value for row in grid for value in row}) == 2
        grid_shapes.add((info["grid_h"], info["grid_w"]))
        bbox_shapes.add((info["bbox_h"], info["bbox_w"]))
        colors.add(info["fg_color"])
        if gen.schedule_profile(seed, index, difficulty=band) == "canonical_core":
            core += 1
            assert (info["grid_h"], info["grid_w"], info["bbox_h"], info["bbox_w"]) == (8, 8, 3, 3)
            assert gen.strict_canonical_like(grid) == []
        else:
            variable += 1
            assert (info["bbox_h"], info["bbox_w"]) != (3, 3)
            assert fixed_3x3_rival(grid) != output
    assert core == variable == 64
    assert len(grid_shapes) >= 12
    assert len(bbox_shapes) >= 8
    assert len(colors) == 9


def test_every_four_pair_lesson_survives_query_rotation():
    for start in range(12):
        pairs = []
        for offset in range(4):
            grid = gen.generate(500 + start, start + offset, difficulty="hard")
            pairs.append({"input": grid, "output": intended_output(grid)})
        for query_index in range(4):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            query = pairs[query_index]
            assert any(fixed_3x3_rival(pair["input"]) != pair["output"] for pair in demos)
            assert gen.lesson_identifiable(demos, {"input": query["input"]}) == []


def test_fixed_3x3_shortcut_fits_canonical_but_exact_witness_refutes_it():
    assert all(fixed_3x3_rival(pair["input"]) == pair["output"] for pair in canonical_pairs())
    grid = witness_input()
    intended = intended_output(grid)
    rival = fixed_3x3_rival(grid)
    assert intended == [[4, 0, 4, 0], [0, 4, 0, 4]]
    assert rival == [
        [4, 0, 0, 4, 0, 0],
        [0, 4, 0, 0, 4, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    assert rival != intended
    assert gen.self_check(grid) == []
    assert gen.SEMANTIC_WITNESSES["variable_bbox"](grid)
    assert gen.SEMANTIC_RIVALS["fixed_3x3_crop"](deepcopy(grid)) == rival
    assert gen.CANONICAL_SHORTCUTS["fixed_3x3_crop"](deepcopy(grid)) == rival


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 8 for _ in range(8)], [[0] * 8 for _ in range(8)]],
)
def test_malformed_grids_are_diagnostic_not_exceptions(grid):
    assert gen.self_check(grid)


def test_python_hash_seed_does_not_change_pixels():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]


def test_real_racket_matches_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()] + [witness_input()]
    grids += [gen.generate(719, index, difficulty="hard") for index in range(16)]
    assert racket_outputs(grids) == [intended_output(grid) for grid in grids]
