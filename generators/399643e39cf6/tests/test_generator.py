"""Regression suite for 399643e39cf6.

The tests use an independent task oracle in workspace/reference_probe.py.  They
exercise the selected generator through GENERATOR_UNDER_TEST when staged by the
review harness, so they remain portable in a fresh packet extraction.
"""
from __future__ import annotations

from copy import deepcopy
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (
    canonical_pairs,
    generated_contract_errors,
    intended_output,
    load_generator,
    racket_outputs,
    rule_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "test0"])
def test_canonical_pairs_remain_owned_and_match_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]


def test_known_marker_ordering_defect_is_absent_from_replayed_seed():
    grid = gen.generate(1, 1, difficulty="easy")
    assert gen.self_check(grid) == []
    assert generated_contract_errors(grid) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_generated_domain_is_deterministic_and_full_copy_lawful(band):
    for index in range(96):
        seed = 1000 + 17 * index
        sample_index = 29 * index + 3
        grid = gen.generate(seed, sample_index, difficulty=band)
        assert grid == gen.generate(seed, sample_index, difficulty=band)
        assert gen.self_check(grid, difficulty=band) == []
        assert generated_contract_errors(grid) == []
        output = intended_output(grid)
        assert output != grid


def test_public_override_product_is_constructive_and_observable():
    axes = {
        "grid_h": (8, 10),
        "grid_w": (9, 11),
        "vector_kind": ("canonical", "horizontal", "down_left", "vertical"),
        "selection_kind": ("unique", "tie"),
        "small_shape": ("domino", "triomino", "tetromino"),
        "large_shape": ("pentomino", "hexomino", "heptomino"),
        "palette_kind": ("canonical", "warm", "cool", "broad"),
    }
    names = tuple(axes)
    for case_index, values in enumerate(itertools.product(*(axes[name] for name in names))):
        options = dict(zip(names, values))
        grid = gen.generate(7000 + case_index, case_index, difficulty="hard", **options)
        assert gen.self_check(grid) == [], options
        assert generated_contract_errors(grid) == [], options
        assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value,error_type",
    [
        ("typo_axis", 1, (KeyError, ValueError)),
        ("grid_h", 7, ValueError),
        ("grid_h", 11, ValueError),
        ("grid_w", 8, ValueError),
        ("grid_w", 12, ValueError),
        ("grid_h", True, TypeError),
        ("grid_w", 9.5, TypeError),
        ("vector_kind", "reverse", ValueError),
        ("selection_kind", "largest", ValueError),
        ("small_shape", "single", ValueError),
        ("large_shape", "square", ValueError),
        ("palette_kind", 3, TypeError),
    ],
)
def test_invalid_overrides_are_rejected(key, value, error_type):
    with pytest.raises(error_type):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("difficulty", ["trivial", 0, True])
def test_invalid_difficulty_is_rejected(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty=difficulty)


def test_four_slot_schedule_is_rotation_safe_against_every_declared_rival():
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.LESSON_SCHEDULE_PERIOD == 4
    assert set(gen.LESSON_COMPETITORS)
    for band in ("easy", "medium", "hard"):
        for start in range(gen.LESSON_SCHEDULE_PERIOD):
            grids = [gen.generate(3301, start + offset, difficulty=band) for offset in range(4)]
            pairs = [{"input": grid, "output": intended_output(grid)} for grid in grids]
            for query_index in range(4):
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                query = pairs[query_index]
                assert gen.lesson_identifiable(demos, query) == []
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert not all(rival(pair["input"]) == pair["output"] for pair in demos), (
                        band,
                        start,
                        query_index,
                        name,
                    )


def test_declared_canonical_shortcuts_really_fit_every_canonical_pair():
    assert {"topmost_object", "lowest_color_object"} <= set(gen.CANONICAL_SHORTCUTS)
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs()), name


def test_each_production_draw_refutes_core_selection_and_copy_shortcuts():
    names = {
        "topmost_object",
        "lowest_color_object",
        "largest_object",
        "all_objects",
        "keep_markers",
        "reverse_vector",
    }
    assert names <= set(gen.LESSON_COMPETITORS)
    for index in range(64):
        grid = gen.generate(901 + index, index)
        expected = intended_output(grid)
        for name in names:
            assert gen.LESSON_COMPETITORS[name](grid) != expected, (index, name)


def test_schedule_supplies_canonical_profile_and_all_axis_profiles_per_band():
    canonical_profiles = {(8, 9, 4), (9, 9, 4)}
    for band in ("easy", "medium", "hard"):
        observed = [gen.observe_overrides(gen.generate(77, index, difficulty=band)) for index in range(4)]
        profiles = {
            (
                len(gen.generate(77, index, difficulty=band)),
                len(gen.generate(77, index, difficulty=band)[0]),
                len({value for row in gen.generate(77, index, difficulty=band) for value in row}),
            )
            for index in range(4)
        }
        assert profiles & canonical_profiles
        assert {row["selection_kind"] for row in observed} == {"unique", "tie"}
        assert {row["vector_kind"] for row in observed} == {
            "canonical",
            "horizontal",
            "down_left",
            "vertical",
        }


@pytest.mark.parametrize(
    "mutation",
    [
        "erase_marker",
        "extra_marker",
        "erase_object",
        "unknown_color_type",
        "clip_selected_copy",
        "occupy_selected_target",
        "too_small_canvas",
    ],
)
def test_validator_rejects_structure_destroying_mutations(mutation):
    grid = gen.generate(51, 2, selection_kind="unique", vector_kind="canonical")
    if mutation == "erase_marker":
        r, c = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9)
        grid[r][c] = 0
    elif mutation == "extra_marker":
        r, c = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 0)
        grid[r][c] = 9
    elif mutation == "erase_object":
        color = min(value for row in grid for value in row if value not in (0, 9))
        for row in grid:
            for c, value in enumerate(row):
                if value == color:
                    row[c] = 0
    elif mutation == "unknown_color_type":
        grid[0][0] = True
    elif mutation == "clip_selected_copy":
        # Replace the marker pair with a canvas-scale vector.  This is
        # guaranteed to clip any multi-cell selected object, independent of
        # the generated layout; the previous adjacent-bottom pair was lawful.
        markers = sorted((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9)
        for r, c in markers:
            grid[r][c] = 0
        grid[0][0] = 9
        grid[-1][-1] = 9
    elif mutation == "occupy_selected_target":
        base = intended_output(grid)
        changed = next(
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == 0 and base[r][c] != 0
        )
        grid[changed[0]][changed[1]] = 1
    elif mutation == "too_small_canvas":
        grid = [row[:-2] for row in grid[:-2]]
    assert gen.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(8)]])
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_independent_oracle_matches_real_racket_on_canonical_and_generated_inputs():
    from arc_repl.racket_bridge import RacketUnavailableError

    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(1200 + i, i, difficulty=("easy", "medium", "hard")[i % 3]) for i in range(32)]
    try:
        outputs = racket_outputs(grids)
    except RacketUnavailableError as exc:
        pytest.skip(str(exc))
    assert outputs == [intended_output(grid) for grid in grids]


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
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
