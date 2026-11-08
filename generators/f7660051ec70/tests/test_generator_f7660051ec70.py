"""Task-local regression contract for seeded-frame interior filling."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    exactly_one_output,
    fill_all_output,
    frames,
    intended_output,
    load_generator,
    observed,
    root,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
EXPECTED_AXES = {
    "grid_h",
    "grid_w",
    "n_seeded_frames",
    "n_decoy_frames",
    "seed_count",
}
CANONICAL_PROFILES = {(10, 12, 3), (11, 13, 3), (12, 14, 3)}


def _pair(grid):
    return {"input": grid, "output": intended_output(grid)}


def _palette_size(grid):
    return len({value for row in grid for value in row})


def test_authority_pin_and_honest_axis_surface():
    assert gen.RULE_HASH == "3efd212303b7"
    assert gen.VERSION == "4.0.0"
    assert set(gen.AXES) == EXPECTED_AXES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.LESSON_SCHEDULE_PERIOD == 2


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(),
    ids=lambda pair: f"{pair['split']}{pair['pair_index']}",
)
def test_canonical_inputs_are_owned_and_mirrored(pair):
    source = deepcopy(pair["input"])
    assert gen.self_check(source) == []
    assert gen.strict_canonical_like(source) == []
    assert intended_output(source) == pair["output"]
    assert gen.rule_mirror(source) == pair["output"]
    assert source == pair["input"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {
            "grid_h": 9,
            "grid_w": 11,
            "n_seeded_frames": 2,
            "n_decoy_frames": 2,
            "seed_count": 2,
        },
        {
            "grid_h": 26,
            "grid_w": 26,
            "n_seeded_frames": 1,
            "n_decoy_frames": 1,
            "seed_count": 1,
        },
        {
            "grid_h": 10,
            "grid_w": 12,
            "n_seeded_frames": 2,
            "n_decoy_frames": 1,
            "seed_count": 1,
        },
    ],
)
def test_exact_overrides_are_constructive_and_observable(band, options):
    grid = gen.generate(1729, 4, difficulty=band, **options)
    assert gen.self_check(grid, meta={"overrides": options}) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert gen.rule_mirror(grid) == intended_output(grid)


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_heigth": 26},
        {"grid_h": 8},
        {"grid_h": 27},
        {"grid_w": 10},
        {"grid_w": 27},
        {"n_seeded_frames": 0},
        {"n_seeded_frames": 3},
        {"n_decoy_frames": 0},
        {"n_decoy_frames": 3},
        {"seed_count": 0},
        {"seed_count": 3},
        {"grid_h": True},
        {"grid_w": "12"},
        {"seed_count": 1.0},
        {"texture": "warm"},
        {"palette_kind": "cool"},
    ],
)
def test_invalid_unknown_and_obsolete_overrides_fail_closed(overrides):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_three_consecutive_samples_teach_one_and_two_seed_cases(band):
    for start in range(12):
        counts = []
        for index in range(start, start + 3):
            grid = gen.generate(700 + start, index, difficulty=band)
            assert gen.self_check(grid) == []
            counts.append(observed(grid)["seed_count"])
        assert set(counts) == {1, 2}


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_is_lawful_diverse_and_canonically_anchored(band):
    shapes = set()
    frame_counts = set()
    seed_counts = set()
    exact_profiles = 0
    for index in range(96):
        grid = gen.generate(8100 + index, index * 11, difficulty=band)
        assert grid == gen.generate(8100 + index, index * 11, difficulty=band)
        assert gen.self_check(grid) == []
        stats = observed(grid)
        shapes.add((stats["grid_h"], stats["grid_w"]))
        frame_counts.add((stats["n_seeded_frames"], stats["n_decoy_frames"]))
        seed_counts.add(stats["seed_count"])
        exact_profiles += (
            stats["grid_h"], stats["grid_w"], _palette_size(grid)
        ) in CANONICAL_PROFILES
        assert intended_output(grid) != grid
        assert fill_all_output(grid) != intended_output(grid)
    assert len(shapes) >= 12
    assert len(frame_counts) >= 3
    assert seed_counts == {1, 2}
    assert exact_profiles >= 8


def test_declared_witnesses_refute_named_rivals():
    one = gen.generate(41, 0, seed_count=1)
    two = gen.generate(41, 1, seed_count=2)
    for grid in (one, two):
        expected = intended_output(grid)
        for witness, rivals in gen.WITNESS_RIVALS.items():
            if gen.SEMANTIC_WITNESSES[witness](grid):
                assert any(gen.SEMANTIC_RIVALS[name](grid) != expected for name in rivals)
    assert gen.SEMANTIC_WITNESSES["two_seed_frame"](two)
    assert exactly_one_output(two) != intended_output(two)
    assert gen.SEMANTIC_WITNESSES["unseeded_decoy"](one)
    assert fill_all_output(one) != intended_output(one)


def test_lesson_contract_accepts_scheduled_window_and_reports_ambiguity():
    scheduled = [_pair(gen.generate(99, index)) for index in range(4)]
    for query_index in range(4):
        demos = [pair for i, pair in enumerate(scheduled) if i != query_index]
        assert gen.lesson_identifiable(demos, scheduled[query_index]) == []

    demos = [_pair(gen.generate(101, index, seed_count=1)) for index in range(3)]
    query = _pair(gen.generate(102, 9, seed_count=2))
    reasons = gen.lesson_identifiable(demos, query)
    assert any("exactly_one_seed" in reason for reason in reasons)


@pytest.mark.parametrize(
    "mutation",
    ["stray_seed", "break_frame", "remove_decoy", "third_seed", "unknown_color"],
)
def test_self_check_rejects_structural_mutations(mutation):
    grid = gen.generate(
        313,
        7,
        grid_h=12,
        grid_w=14,
        n_seeded_frames=1,
        n_decoy_frames=1,
        seed_count=2,
    )
    parsed = frames(grid)
    seeded = next(frame for frame in parsed if frame["seed_count"])
    decoy = next(frame for frame in parsed if not frame["seed_count"])
    if mutation == "stray_seed":
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value == 0 and not any(
                    f["r1"] < r < f["r2"] and f["c1"] < c < f["c2"]
                    for f in parsed
                ):
                    grid[r][c] = 2
                    break
            else:
                continue
            break
    elif mutation == "break_frame":
        grid[seeded["r1"]][seeded["c1"]] = 0
    elif mutation == "remove_decoy":
        r = decoy["r1"] + 1
        c = decoy["c1"] + 1
        grid[r][c] = 2
    elif mutation == "third_seed":
        for r in range(seeded["r1"] + 1, seeded["r2"]):
            for c in range(seeded["c1"] + 1, seeded["c2"]):
                if grid[r][c] == 0:
                    grid[r][c] = 2
                    break
            else:
                continue
            break
    else:
        grid[0][0] = 9
    assert gen.self_check(grid)


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True] * 11 for _ in range(9)]])
def test_malformed_grid_is_diagnostic_not_exception(bad):
    assert gen.self_check(bad)


def test_generated_inputs_match_real_racket_authority():
    from arcpuzzles import Catalog

    grids = [
        gen.generate(601, index, difficulty=band)
        for band in ("easy", "medium", "hard")
        for index in range(4)
    ]
    receipt = Catalog(root()).apply(gen.TASK_ID, grids, reference="canonical", timeout=180)
    assert receipt["rule_hash_matches_catalog"]
    assert [item["output"] for item in receipt["results"]] == [
        intended_output(grid) for grid in grids
    ]


def test_generation_is_independent_of_python_hash_seed():
    source = str(Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")))
    script = (
        "import importlib.util,json,sys;"
        "s=importlib.util.spec_from_file_location('g',sys.argv[1]);"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "print(json.dumps(m.generate(31337,19,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "777"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output([sys.executable, "-B", "-c", script, source], env=env, text=True)
        )
    assert outputs[0] == outputs[1]
