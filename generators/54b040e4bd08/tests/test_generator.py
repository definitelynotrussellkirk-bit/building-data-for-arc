"""Task-local regression tests for the 2D periodic-hole sampler."""
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
from reference_probe import (  # noqa: E402
    canonical_pairs,
    column_only_output,
    load_generator,
    observed,
    reference_output,
    row_only_output,
    top_left_output,
)

gen = load_generator()


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "test0"])
def test_canonical_pairs_are_owned_and_match_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert reference_output(pair["input"]) == pair["output"]


def test_rule_hash_and_schedule_contract_are_pinned():
    assert gen.RULE_HASH == "55b239af8777"
    assert gen.LESSON_SCHEDULE_PERIOD == 4
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "row_gap_a", "column_gap_a", "row_gap_b", "column_gap_b"
    )


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        dict(grid_h=6, grid_w=9, tile_shape="2x2", vertical_margin=1, horizontal_margin=1),
        dict(grid_h=10, grid_w=12, tile_shape="2x3", vertical_margin=2, horizontal_margin=2),
        dict(grid_h=9, grid_w=10, tile_shape="3x2", vertical_margin=1, horizontal_margin=2),
    ],
)
def test_exact_overrides_are_observable_in_every_band(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    expected = dict(options)
    assert gen.observe_overrides(grid) == expected
    assert {key: observed(grid)[key] for key in expected} == expected


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 5), ("grid_h", 11), ("grid_h", True), ("grid_h", 8.0),
        ("grid_w", 8), ("grid_w", 13),
        ("tile_shape", "3x3"), ("tile_shape", 23),
        ("vertical_margin", 0), ("vertical_margin", 3),
        ("horizontal_margin", 0), ("horizontal_margin", 3),
    ],
)
def test_invalid_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("sample_index", range(12))
def test_default_schedule_is_exact_lawful_and_deterministic(sample_index):
    first = gen.generate(811, sample_index, difficulty="hard")
    second = gen.generate(811, sample_index, difficulty="hard")
    assert first == second
    assert gen.self_check(first) == []
    profile = gen.schedule_profile(811, sample_index, "hard")
    assert profile == gen.SCHEDULE_PROFILES[sample_index % 4]
    assert gen.observe_overrides(first) == gen.PROFILE_SPECS[profile]
    assert reference_output(first) != first


def test_each_four_pair_window_is_rotation_safe_against_declared_rivals():
    pairs = []
    for index in range(8):
        grid = gen.generate(33, index, difficulty="medium")
        pairs.append({"input": grid, "output": reference_output(grid)})
    for start in range(4):
        lesson = [pairs[(start + offset) % 4] for offset in range(4)]
        for query_index in range(4):
            demos = [pair for index, pair in enumerate(lesson) if index != query_index]
            query = lesson[query_index]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_declared_canonical_shortcuts_fit_every_canonical_pair():
    shortcuts = {
        "row_only": row_only_output,
        "column_only": column_only_output,
        "top_left_tile": top_left_output,
    }
    assert set(gen.CANONICAL_SHORTCUTS) == set(shortcuts)
    for pair in canonical_pairs():
        for name, shortcut in shortcuts.items():
            assert shortcut(pair["input"]) == pair["output"], name
            assert gen.CANONICAL_SHORTCUTS[name](pair["input"]) == pair["output"], name


@pytest.mark.parametrize("sample_index", range(8))
def test_default_schedule_supplies_real_generated_shortcut_counterexamples(sample_index):
    grid = gen.generate(91, sample_index)
    answer = reference_output(grid)
    assert gen.CANONICAL_SHORTCUTS["top_left_tile"](grid) != answer
    if sample_index % 2 == 0:
        assert gen.CANONICAL_SHORTCUTS["row_only"](grid) != answer
    else:
        assert gen.CANONICAL_SHORTCUTS["column_only"](grid) != answer


@pytest.mark.parametrize(
    "mutation",
    ["extra_color", "blank", "drop_color", "duplicate_last_row", "split_hole"],
)
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(4, 2)
    if mutation == "extra_color":
        grid[0][0] = next(color for color in range(1, 10) if color not in {v for row in grid for v in row})
    elif mutation == "blank":
        grid = [[0 for _ in row] for row in grid]
    elif mutation == "drop_color":
        color = min(v for row in grid for v in row if v)
        grid = [[0 if value == color else value for value in row] for row in grid]
    elif mutation == "duplicate_last_row":
        grid[-1] = list(grid[0])
    elif mutation == "split_hole":
        grid[0][0] = 0
    assert gen.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(6)]])
def test_malformed_inputs_return_diagnostics_not_exceptions(grid):
    assert gen.self_check(grid)


def test_generated_outputs_match_real_racket_reference_when_available():
    from arc_repl.racket_bridge import racket_runtime_status
    try:
        from arcpuzzles import Catalog
    except ModuleNotFoundError:
        pytest.skip("staged arcpuzzles package required for authority parity")

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [gen.generate(319, index) for index in range(12)]
    receipt = Catalog(HOME.parents[1]).apply(gen.TASK_ID, grids, timeout=120)
    assert receipt["rule_hash_matches_catalog"]
    assert [item["output"] for item in receipt["results"]] == [
        reference_output(grid) for grid in grids
    ]


def test_keyed_palette_rng_is_independent_of_python_hash_seed():
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


def test_difficulty_bands_are_observably_distinct_without_geometry_drift():
    grids = [gen.generate(777, 0, difficulty=band) for band in ("easy", "medium", "hard")]
    assert len({repr(grid) for grid in grids}) == 3
    assert len({repr(gen.observe_overrides(grid)) for grid in grids}) == 1


@pytest.mark.parametrize("sample_index", range(4))
def test_default_hole_is_a_non_modal_adversarial_stripe(sample_index):
    grid = gen.generate(55, sample_index)
    counts = {color: sum(value == color for row in grid for value in row)
              for color in range(10)}
    assert 1 <= counts[0] <= 10
    assert counts[0] < max(counts[color] for color in range(1, 10))


def test_retained_top_left_shortcut_counterexample_is_racket_bound():
    counterexamples = HOME / "counterexamples"
    grid = json.loads((counterexamples / "top_left_tile_input.json").read_text())
    rival = json.loads((counterexamples / "top_left_tile_rival.json").read_text())
    receipt = json.loads((counterexamples / "top_left_tile_racket.json").read_text())
    intended = receipt["results"][0]["output"]
    assert receipt["executed_rule_hash"] == gen.RULE_HASH
    assert receipt["generator_sha256"] == "cda17d37aca36d09fee0d424e3d959f19048f7c5f65e15637fc4d73fd20a835f"
    assert gen.self_check(grid) == []
    assert intended == reference_output(grid)
    assert rival == gen.CANONICAL_SHORTCUTS["top_left_tile"](grid)
    assert rival != intended
