"""Regression suite for the bc932ac8117a hole-transfer curriculum."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from reviewer_support import canonical_pairs, find_root

ROOT = find_root(__file__)
HOME = ROOT / "generators/bc932ac8117a"
sys.path.insert(0, str(HOME / "workspace"))
from hole_transfer_probe import (analyze, expected_pattern, load_generator, observed,
                                 racket_outputs, true_output, witness_input)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
PAIRS = canonical_pairs("bc932ac8117a", root=ROOT)
AXES = {"grid_h", "grid_w", "box_size", "palette_kind", "hollow_side", "hole_diagonal"}


def test_metadata_pins_authority_and_declares_only_exact_controls():
    assert gen.RULE_HASH == "bcafd3a4dd95"
    assert gen.EXAMPLES_NEEDED == 3
    assert set(gen.AXES) == AXES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert callable(gen.observe_overrides)
    assert callable(gen.strict_canonical_like)
    assert callable(gen.rule_mirror)
    assert callable(gen.lesson_identifiable)


@pytest.mark.parametrize("pair", PAIRS, ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_accepts_canonical_inputs_and_independent_oracle_matches_labels(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert true_output(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height,width", [(5, 11), (16, 22)])
@pytest.mark.parametrize("size", [4, 5])
@pytest.mark.parametrize("palette", ["default", "warm", "cool", "varied"])
@pytest.mark.parametrize("side", ["left", "right"])
@pytest.mark.parametrize("diagonal", ["main", "anti"])
def test_every_exact_override_boundary_is_constructive_and_observable(
    band, height, width, size, palette, side, diagonal
):
    requested = {
        "grid_h": height,
        "grid_w": width,
        "box_size": size,
        "palette_kind": palette,
        "hollow_side": side,
        "hole_diagonal": diagonal,
    }
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert observed(grid) == requested
    assert gen.observe_overrides(grid) == requested
    assert gen.rule_mirror(grid) == true_output(grid)


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 4), ("grid_h", 17), ("grid_h", True), ("grid_h", 5.0),
        ("grid_w", 10), ("grid_w", 23), ("grid_w", "11"),
        ("box_size", 3), ("box_size", 6), ("box_size", False),
        ("palette_kind", "missing"), ("palette_kind", 3),
        ("hollow_side", "top"), ("hollow_side", 0),
        ("hole_diagonal", "vertical"), ("hole_diagonal", 1),
    ],
)
def test_rejects_unknown_invalid_and_coercible_overrides(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize(
    "seed,sample_index,difficulty",
    [
        (True, 0, None), (1.0, 0, None), ("1", 0, None),
        (1, True, None), (1, -1, None), (1, 1.0, None), (1, "1", None),
        (1, 0, True), (1, 0, 0), (1, 0, 1.0),
        (1, 0, "__invalid_difficulty__"),
    ],
)
def test_rejects_invalid_call_scalars(seed, sample_index, difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index, difficulty=difficulty)


def test_consecutive_default_examples_alternate_hollow_side():
    for seed in range(32):
        sides = [observed(gen.generate(seed, index))["hollow_side"] for index in range(8)]
        assert sides == ["left", "right"] * 4


def test_twins_share_top_row_so_side_alternation_controls_raster_order():
    for band in (None, "easy", "medium", "hard"):
        for seed in range(32):
            for index in range(4):
                hollow, solid, _ = analyze(gen.generate(seed, index, difficulty=band))
                assert hollow["bbox"][0] == solid["bbox"][0]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_generated_cases_are_valid_deterministic_and_teach_both_shortcuts(band):
    grids = [gen.generate(900 + index, index * 7 + 3, difficulty=band) for index in range(96)]
    assert grids == [gen.generate(900 + index, index * 7 + 3, difficulty=band)
                     for index in range(96)]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in grids}) >= 88
    sides, diagonals, sizes, palettes = set(), set(), set(), set()
    for grid in grids:
        assert gen.self_check(grid) == []
        stats = observed(grid)
        sides.add(stats["hollow_side"])
        diagonals.add(stats["hole_diagonal"])
        sizes.add(stats["box_size"])
        palettes.add(stats["palette_kind"])
        hollow, _, holes = analyze(grid)
        assert len(holes) >= 2
        assert gen.SEMANTIC_WITNESSES["partial_hole_pattern"](grid)
        assert gen.SEMANTIC_WITNESSES["multiple_holes"](grid)
        intended = true_output(grid)
        assert gen.SEMANTIC_RIVALS["carve_full_interior"](grid) != intended
        assert gen.SEMANTIC_RIVALS["largest_hole_only"](grid) != intended
        assert gen.rule_mirror(grid) == intended
    assert sides == {"left", "right"}
    assert diagonals == {"main", "anti"}
    assert sizes == {4, 5}
    assert palettes == {"default", "warm", "cool", "varied"}


def test_explicit_shortcut_counterexample_has_exact_disagreements():
    grid = witness_input()
    assert gen.self_check(grid) == []
    intended = true_output(grid)
    full = gen.SEMANTIC_RIVALS["carve_full_interior"](grid)
    largest = gen.SEMANTIC_RIVALS["largest_hole_only"](grid)
    assert intended != full
    assert intended != largest
    assert sum(a != b for row_a, row_b in zip(intended, full)
               for a, b in zip(row_a, row_b)) == 2
    assert sum(a != b for row_a, row_b in zip(intended, largest)
               for a, b in zip(row_a, row_b)) == 1


def test_retained_counterexample_replays_the_two_shortcut_failures():
    path = HOME / "counterexamples/review-23d35f89d6394ad3/canonical-shortcuts.json"
    data = json.loads(path.read_text())
    grid = data["input"]
    assert grid == witness_input()
    assert data["intended_output"] == true_output(grid)
    assert data["rival_outputs"]["carve_full_interior"] == (
        gen.SEMANTIC_RIVALS["carve_full_interior"](grid)
    )
    assert data["rival_outputs"]["largest_hole_only"] == (
        gen.SEMANTIC_RIVALS["largest_hole_only"](grid)
    )
    assert data["cell_disagreements"] == {
        "carve_full_interior": 2,
        "largest_hole_only": 1,
    }


def test_every_query_rotation_refutes_declared_competitors_and_position_gating():
    assert "rightmost_target_only" in gen.CANONICAL_SHORTCUTS
    for pair in PAIRS:
        assert gen.CANONICAL_SHORTCUTS["rightmost_target_only"](pair["input"]) == pair["output"]
    for band in (None, "easy", "medium", "hard"):
        for start in range(24):
            materialized = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(700 + start, start + offset, difficulty=band)
                materialized.append({"input": grid, "output": true_output(grid)})
            for query_index, query in enumerate(materialized):
                demos = materialized[:query_index] + materialized[query_index + 1:]
                assert {observed(pair["input"])["hollow_side"] for pair in demos} == {"left", "right"}
                assert gen.lesson_identifiable(demos, query) == []
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


@pytest.mark.parametrize("mutation", ["missing_twin", "size_mismatch", "no_hole", "stray_pixel", "broken_frame"])
def test_structural_validator_rejects_known_impostors(mutation):
    grid = witness_input()
    if mutation == "missing_twin":
        for row in range(4):
            for col in range(5, 9):
                grid[row][col] = 0
    elif mutation == "size_mismatch":
        for col in range(5, 9):
            grid[3][col] = 0
    elif mutation == "no_hole":
        for row in range(1, 3):
            for col in range(1, 3):
                grid[row][col] = 2
    elif mutation == "stray_pixel":
        grid[4][10] = 2
    elif mutation == "broken_frame":
        grid[0][1] = 0
    assert gen.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 11 for _ in range(5)]])
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_rule_and_rivals_are_input_pure():
    grid = gen.generate(44, 13, difficulty="hard")
    before = deepcopy(grid)
    gen.rule_mirror(grid)
    for rival in gen.SEMANTIC_RIVALS.values():
        rival(grid)
    assert grid == before


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from hole_transfer_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    results = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(subprocess.check_output(
            [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
            env=env, text=True,
        ))
    assert results[0] == results[1]


def test_real_racket_authority_on_canonical_witness_and_generated_inputs():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in PAIRS] + [witness_input()]
    grids += [gen.generate(1701 + index, index) for index in range(16)]
    assert racket_outputs(grids) == [true_output(grid) for grid in grids]
