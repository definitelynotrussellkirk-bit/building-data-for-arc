"""Task-local regression suite for generator 9ee024f29fdb."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (
    CANONICAL_SHAPES,
    authority_output,
    canonical_pairs,
    cyclic_lesson_summary,
    distribution_summary,
    interior_cells,
    interior_eight_count,
    is_strict_canonical_profile,
    lattice_cells,
    load_generator,
    observed_exact_axes,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def _pair(grid):
    return {"input": grid, "output": authority_output(grid)}


@pytest.mark.parametrize("layout", gen.EIGHT_LAYOUTS)
def test_every_layout_realizes_requested_interior_eight_count(layout):
    density = 0.55
    grid = gen.generate(
        1701,
        4,
        grid_h=17,
        grid_w=17,
        eight_density=density,
        eight_layout=layout,
        decoy_palette_size=0,
    )
    expected = max(1, int(len(interior_cells(grid)) * density))
    assert interior_eight_count(grid) == expected


def test_canonical_rule_hash_is_pinned():
    assert getattr(gen, "RULE_HASH", None) == "82f439b3efb8"


def test_runtime_rule_source_is_textually_synchronized_with_canonical():
    root = HOME.parents[1]
    with (root / "shared/data/canonical/puzzles.jsonl").open() as handle:
        canonical = next(
            json.loads(line)["program_solution"]
            for line in handle
            if json.loads(line).get("task_id") == gen.TASK_ID
        )
    base = json.loads(
        (root / "shared/data/base/solutions/training/1c0d0a4b__9ee024f29fdb.json").read_text()
    )["racket_target"]
    normalize = lambda text: " ".join(text.split())
    assert normalize(base["raw_code"]) == normalize(canonical)
    assert normalize(base["target_code"]) == normalize(canonical)


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "train2", "test0"])
def test_canonical_inputs_are_accepted_and_match_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert authority_output(pair["input"]) == pair["output"]
    assert hasattr(gen, "strict_canonical_like")
    assert gen.strict_canonical_like(pair["input"]) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_observable_in_every_band(band):
    options = {
        "grid_h": 17,
        "grid_w": 5,
        "decoy_palette_size": 2,
        "lattice_noise": True,
    }
    grid = gen.generate(
        431,
        9,
        difficulty=band,
        eight_density=0.55,
        eight_layout="column",
        **options,
    )
    assert gen.self_check(grid) == []
    assert observed_exact_axes(grid) == options
    assert hasattr(gen, "observe_overrides")
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("texture", "all_eights"),
        ("grid_h", 6),
        ("grid_h", True),
        ("grid_w", "9"),
        ("decoy_palette_size", -1),
        ("decoy_palette_size", 3),
        ("decoy_palette_size", 1.5),
        ("lattice_noise", 1),
        ("lattice_noise", "true"),
        ("eight_density", 0.09),
        ("eight_density", 0.81),
        ("eight_density", "0.5"),
        ("eight_layout", "diagonal"),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


def test_schedule_alternates_core_and_joint_counterexample_profiles():
    assert hasattr(gen, "schedule_profile")
    assert getattr(gen, "SCHEDULE_PROFILES", ()) == (
        "canonical_core",
        "joint_counterexample",
    )
    profiles = [gen.schedule_profile(7, index, "hard") for index in range(8)]
    assert profiles == ["canonical_core", "joint_counterexample"] * 4

    core = gen.generate(7, 0, grid_h=9, grid_w=13, eight_layout="random")
    counter = gen.generate(7, 1, grid_h=9, grid_w=13, eight_layout="random")
    assert observed_exact_axes(core)["decoy_palette_size"] == 0
    assert observed_exact_axes(core)["lattice_noise"] is False
    assert observed_exact_axes(counter)["decoy_palette_size"] in (1, 2)
    assert observed_exact_axes(counter)["lattice_noise"] is True
    # Every periodic row and column must be visibly nonzero in the counterexample,
    # defeating the tempting "detect all-zero lines" shortcut.
    assert all(any(value != 0 for value in counter[r]) for r in range(0, len(counter), 4))
    assert all(any(counter[r][c] != 0 for r in range(len(counter))) for c in range(0, len(counter[0]), 4))


def test_generated_inputs_are_deterministic_lawful_and_nontrivial():
    for band in (None, "easy", "medium", "hard"):
        for index in range(96):
            grid = gen.generate(9000 + index, 11 * index + 1, difficulty=band)
            assert grid == gen.generate(9000 + index, 11 * index + 1, difficulty=band)
            assert gen.self_check(grid) == []
            original = deepcopy(grid)
            output = authority_output(grid)
            assert grid == original
            assert output != grid
            assert {0, 2} <= {value for row in output for value in row}


def test_default_distribution_has_canonical_support_in_every_band():
    assert hasattr(gen, "MIN_STRICT_FRAC")
    summary = distribution_summary(gen, count=96)
    for row in summary.values():
        assert set(row["profiles"]) == set(gen.SCHEDULE_PROFILES)
        assert row["strict"] / row["samples"] >= gen.MIN_STRICT_FRAC
        assert any(shape in CANONICAL_SHAPES for shape in row["shapes"])
        assert row["decoy_counts"][0] > 0
        assert row["decoy_counts"][1] + row["decoy_counts"][2] > 0
        assert row["lattice_noise"][False] > 0
        assert row["lattice_noise"][True] > 0


@pytest.mark.parametrize(
    "bad",
    [
        None,
        [],
        [[]],
        [[0], [0, 8]],
        [[True] * 5 for _ in range(5)],
        [[0] * 5 for _ in range(4)],
        [[0] * 6 for _ in range(5)],
        [[0] * 5 for _ in range(5)],
    ],
)
def test_self_check_rejects_malformed_or_signal_free_inputs(bad):
    assert gen.self_check(bad)


def test_self_check_rejects_all_erased_and_accepts_generalized_lawful_input():
    all_eights = [[0] * 5 for _ in range(5)]
    for r in range(5):
        for c in range(5):
            if r % 4 and c % 4:
                all_eights[r][c] = 8
    assert gen.self_check(all_eights)

    generalized = gen.generate(
        12,
        1,
        grid_h=13,
        grid_w=17,
        decoy_palette_size=2,
        lattice_noise=True,
    )
    assert gen.self_check(generalized) == []
    assert hasattr(gen, "strict_canonical_like")
    assert gen.strict_canonical_like(generalized)


def test_observer_matches_independent_grid_observation():
    assert hasattr(gen, "observe_overrides")
    for index in range(64):
        grid = gen.generate(37, index)
        assert gen.observe_overrides(grid) == observed_exact_axes(grid)


def test_declared_rivals_fit_or_fail_where_claimed():
    assert hasattr(gen, "SEMANTIC_WITNESSES")
    assert hasattr(gen, "SEMANTIC_RIVALS")
    assert hasattr(gen, "WITNESS_RIVALS")
    assert hasattr(gen, "CANONICAL_SHORTCUTS")
    assert hasattr(gen, "LESSON_COMPETITORS")

    for pair in canonical_pairs():
        for rival in gen.CANONICAL_SHORTCUTS.values():
            assert rival(pair["input"]) == pair["output"]

    core = gen.generate(101, 0, grid_h=9, grid_w=13)
    counter = gen.generate(101, 1, grid_h=9, grid_w=13)
    grids = [core, counter]
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        witnessed = [grid for grid in grids if gen.SEMANTIC_WITNESSES[witness_name](grid)]
        assert witnessed, witness_name
        for rival_name in rival_names:
            assert any(
                gen.SEMANTIC_RIVALS[rival_name](grid) != authority_output(grid)
                for grid in witnessed
            ), (witness_name, rival_name)

    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert rival(counter) != authority_output(counter), name


def test_three_demos_identify_competitors_under_every_cyclic_query_rotation():
    assert getattr(gen, "EXAMPLES_NEEDED", None) == 3
    assert hasattr(gen, "lesson_identifiable")
    report = cyclic_lesson_summary(gen, starts_per_band=100, seed_base=808)
    assert report["passed"] is True
    assert report["totals"] == {
        "bands": 3,
        "starts": 300,
        "query_rotations": 1200,
        "failures": 0,
    }

    ambiguous = [
        _pair(gen.generate(808, index)) for index in (0, 2, 4)
    ]
    reasons = gen.lesson_identifiable(ambiguous, _pair(gen.generate(808, 6)))
    assert any("fits every demonstration" in reason for reason in reasons)


def test_keyed_generation_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,9,difficulty='hard')))"
    )
    results = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert results[0] == results[1]
