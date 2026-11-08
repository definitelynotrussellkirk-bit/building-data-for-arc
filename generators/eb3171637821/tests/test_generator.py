"""Task-local regression suite for eb3171637821."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (
    analyze,
    canonical_pairs,
    canonical_rule_source,
    geometry_output,
    line_count_rival,
    load_generator,
    racket_outputs,
    witness_input,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs())
def test_accepts_every_canonical_pair_and_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert geometry_output(pair["input"]) == pair["output"]


def test_rule_hash_pins_selected_canonical_authority():
    expected = hashlib.sha256(" ".join(canonical_rule_source().split()).encode()).hexdigest()[:12]
    assert gen.RULE_HASH == expected


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_observable_in_every_band(band):
    requested = {
        "row_bands": 4,
        "col_bands": 5,
        "row_divider_thickness": 2,
        "col_divider_thickness": 2,
        "row_boundary_mode": "both",
        "col_boundary_mode": "start",
    }
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert {key: analyze(grid)[key] for key in requested} == requested


@pytest.mark.parametrize("row_mode", ["none", "start", "end", "both"])
@pytest.mark.parametrize("col_mode", ["none", "start", "end", "both"])
@pytest.mark.parametrize("row_thickness", [1, 2])
@pytest.mark.parametrize("col_thickness", [1, 2])
def test_all_boundary_and_thickness_combinations_construct(row_mode, col_mode, row_thickness, col_thickness):
    requested = {
        "row_bands": 3,
        "col_bands": 4,
        "row_divider_thickness": row_thickness,
        "col_divider_thickness": col_thickness,
        "row_boundary_mode": row_mode,
        "col_boundary_mode": col_mode,
    }
    grid = gen.generate(91, 7, difficulty="hard", **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert geometry_output(grid) == [[analyze(grid)["cell_color"]] * 4 for _ in range(3)]


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("row_bands", 1),
        ("row_bands", 9),
        ("col_bands", True),
        ("row_divider_thickness", 0),
        ("col_divider_thickness", 3),
        ("row_boundary_mode", "left"),
        ("col_boundary_mode", 1),
    ],
)
def test_invalid_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


def test_every_three_demo_window_refutes_line_count_rival():
    """The production consecutive sampler must teach run-counting in every lesson."""
    cases = [
        (2919827526, 25, "easy"),  # retained ambiguity from the first 300-lesson census
        (917263, 0, "easy"),
        (917263, 0, "medium"),
        (917263, 0, "hard"),
    ]
    for seed, first_start, band in cases:
        for start in range(first_start, first_start + 12):
            demos = [gen.generate(seed, start + offset, difficulty=band) for offset in range(3)]
            assert any(line_count_rival(grid) != geometry_output(grid) for grid in demos)


def test_default_distribution_keeps_cell_color_modal_and_divider_connected():
    """Match canonical morphology: the divider lattice is one non-modal object."""
    for band in ("easy", "medium", "hard"):
        for index in range(80):
            grid = gen.generate(6100 + index, index * 17, difficulty=band)
            info = analyze(grid)
            counts = Counter(value for row in grid for value in row)
            assert counts[info["cell_color"]] > counts[info["divider_color"]]


def test_default_distribution_exercises_repaired_branches_in_every_band():
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]), len({v for row in pair["input"] for v in row}))
        for pair in canonical_pairs()
    }
    for band in ("easy", "medium", "hard"):
        observations = []
        profiles = set()
        grids = []
        for index in range(160):
            grid = gen.generate(2100 + index, index * 11, difficulty=band)
            grids.append(grid)
            assert gen.self_check(grid) == []
            assert grid == gen.generate(2100 + index, index * 11, difficulty=band)
            observations.append(gen.observe_overrides(grid))
            profiles.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
        assert any(obs["row_divider_thickness"] == 2 for obs in observations)
        assert any(obs["col_divider_thickness"] == 2 for obs in observations)
        assert any(obs["row_boundary_mode"] != "none" for obs in observations)
        assert any(obs["col_boundary_mode"] != "none" for obs in observations)
        assert profiles & canonical_profiles
        assert len({json.dumps(grid, separators=(",", ":")) for grid in grids}) > 140


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[5, 5], [5, 5]],
        [[8, 8], [8, 5]],
        [[8, 8, 8], [5, 5, 5], [5, 5, 5]],
        [[8, 8, 8], [8, 5, 5], [8, 5, 3]],
    ],
)
def test_validator_rejects_minimal_impostors(grid):
    assert gen.self_check(grid)


def test_strongest_canonical_rival_and_explicit_counterexample():
    pairs = canonical_pairs()
    assert all(line_count_rival(pair["input"]) == pair["output"] for pair in pairs)
    grid = witness_input()
    assert gen.self_check(grid) == []
    assert geometry_output(grid) == [[5, 5], [5, 5]]
    assert line_count_rival(grid) != geometry_output(grid)
    assert gen.CANONICAL_SHORTCUTS["count_individual_divider_lines"](grid) == line_count_rival(grid)
    assert gen.SEMANTIC_WITNESSES["thick_divider_run"](grid)


def test_real_racket_reference_on_canonical_and_repaired_witness():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()] + [witness_input()]
    assert racket_outputs(grids) == [geometry_output(grid) for grid in grids]


def test_generation_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    outputs = []
    for seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]
