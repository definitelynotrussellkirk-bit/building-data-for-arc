"""Regression frontier for the worked-example row/column-closure task."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    always_column_output,
    always_row_output,
    canonical_pairs,
    copy_query_output,
    load_generator,
    observed,
    palette_size,
    rule_output,
    solid_bbox_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
EXPECTED_AXES = {"grid_h", "example_w", "query_w", "mode"}


def _pair(grid):
    return {"input": grid, "output": rule_output(grid)}


def test_authority_pin_and_honest_axis_surface():
    assert gen.RULE_HASH == "25622d47ca31"
    assert gen.VERSION == "3.0.0"
    assert gen.EXAMPLES_NEEDED == 3
    assert set(gen.AXES) == EXPECTED_AXES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(),
    ids=lambda pair: f"{pair['split']}{pair['pair_index']}",
)
def test_every_canonical_pair_is_owned_and_mirrored(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert rule_output(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 6, "example_w": 3, "query_w": 3, "mode": 0},
        {"grid_h": 20, "example_w": 8, "query_w": 12, "mode": 1},
        {"grid_h": 9, "example_w": 7, "query_w": 7, "mode": 0},
        {"grid_h": 9, "example_w": 7, "query_w": 7, "mode": 1},
    ],
)
def test_every_exact_override_combination_is_constructive_and_observable(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert len(grid) <= 30 and len(grid[0]) <= 30
    assert gen.self_check(grid, meta={"overrides": options}) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert gen.rule_mirror(grid) == rule_output(grid)
    assert rule_output(grid) != copy_query_output(grid)
    assert rule_output(grid) != solid_bbox_output(grid)


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"grid_h": 5},
        {"grid_h": 21},
        {"example_w": 2},
        {"example_w": 9},
        {"query_w": 2},
        {"query_w": 13},
        {"mode": -1},
        {"mode": 2},
        {"grid_h": True},
        {"example_w": 3.0},
        {"query_w": "7"},
        {"mode": False},
        {"texture": "default"},
        {"density": "sparse"},
        {"n_distinct_colors": 4},
    ],
)
def test_invalid_unknown_and_obsolete_overrides_fail_closed(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_lawful_identifying_and_canonically_anchored(band):
    modes = set()
    shapes = set()
    canonical_hits = 0
    for index in range(120):
        grid = gen.generate(8100 + index, index, difficulty=band)
        assert grid == gen.generate(8100 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert len(grid) <= 30 and len(grid[0]) <= 30
        facts = observed(grid)
        modes.add(facts["mode"])
        shapes.add((len(grid), len(grid[0]), len(rule_output(grid)), len(rule_output(grid)[0])))
        canonical_hits += (len(grid), len(grid[0]), palette_size(grid)) == (9, 23, 4)
        assert rule_output(grid) != copy_query_output(grid)
        assert rule_output(grid) != solid_bbox_output(grid)
        assert always_row_output(grid) != always_column_output(grid)
    assert modes == {0, 1}
    assert len(shapes) >= 20
    assert canonical_hits >= 20


def test_declared_witnesses_refute_their_named_rivals():
    row = gen.generate(71, 0, grid_h=9, example_w=7, query_w=7, mode=0)
    col = gen.generate(72, 1, grid_h=9, example_w=7, query_w=7, mode=1)
    for grid in (row, col):
        expected = rule_output(grid)
        for witness, rival_names in gen.WITNESS_RIVALS.items():
            if gen.SEMANTIC_WITNESSES[witness](grid):
                for name in rival_names:
                    assert gen.SEMANTIC_RIVALS[name](grid) != expected, (witness, name)
    assert gen.SEMANTIC_WITNESSES["row_mode_refutes_always_column"](row)
    assert gen.SEMANTIC_WITNESSES["column_mode_refutes_always_row"](col)
    assert gen.SEMANTIC_WITNESSES["closure_changes_query"](row)
    assert gen.SEMANTIC_WITNESSES["non_rectangular_result_refutes_solid_bbox"](col)


def test_solid_bbox_is_a_real_canonical_shortcut_but_generated_data_refutes_it():
    assert all(solid_bbox_output(pair["input"]) == pair["output"] for pair in canonical_pairs())
    assert "solid_bbox" in gen.CANONICAL_SHORTCUTS
    for mode in (0, 1):
        grid = gen.generate(505, mode, mode=mode)
        assert gen.CANONICAL_SHORTCUTS["solid_bbox"](grid) != rule_output(grid)


def test_every_four_pair_window_and_rotation_is_identifiable():
    for band in (None, "easy", "medium", "hard"):
        for start in range(12):
            pairs = [
                _pair(gen.generate(9000 + start, start + offset, difficulty=band))
                for offset in range(4)
            ]
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert gen.lesson_identifiable(demos, pairs[query_index]) == []


def test_lesson_hook_reports_an_always_row_shortcut_when_demos_do_not_refute_it():
    demos = [
        _pair(gen.generate(12, index, mode=0))
        for index in range(3)
    ]
    query = _pair(gen.generate(13, 9, mode=1))
    reasons = gen.lesson_identifiable(demos, query)
    assert any("always_row" in reason for reason in reasons)


def test_generation_is_independent_of_python_hash_seed():
    script = (
        "import importlib.util,json,sys;"
        "p=sys.argv[1];s=importlib.util.spec_from_file_location('g',p);"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "print(json.dumps(m.generate(31337,19,difficulty='hard')))"
    )
    path = str(Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")))
    outputs = []
    for hash_seed in ("1", "777"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(subprocess.check_output([sys.executable, "-B", "-c", script, path], env=env, text=True))
    assert outputs[0] == outputs[1]
