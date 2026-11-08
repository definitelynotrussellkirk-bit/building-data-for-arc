"""Task-local regression tests for 4e05481a2c21.

The workspace probe is deliberately independent of production helpers, while
canonical data is located through reviewer_support for portable staging.
"""
from __future__ import annotations

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
from reference_probe import (  # noqa: E402
    all_bbox_zeros_rival,
    canonical_pairs,
    fill_hole_bbox_rival,
    has_exterior_bbox_zero,
    largest_region_rival,
    load_generator,
    make_labeled,
    object_records,
    observed,
    reference_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
EXPECTED_AXES = {"grid_h", "grid_w", "palette_kind", "pattern_kind"}
EXPECTED_SHORTCUTS = {"fill_hole_bbox", "largest_region_only", "all_bbox_zeros"}


def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def test_rule_pin_and_exact_axis_contract():
    assert gen.RULE_HASH == "e13b35a51ff4"
    assert set(gen.AXES) == EXPECTED_AXES
    assert not getattr(gen, "DEGENERATE_TEXTURES", ())
    assert not getattr(gen, "HELPFUL_TEXTURES", ())
    assert gen.EXAMPLES_NEEDED == 4
    assert set(gen.CANONICAL_SHORTCUTS) == EXPECTED_SHORTCUTS
    assert set(gen.LESSON_COMPETITORS) == EXPECTED_SHORTCUTS


@pytest.mark.parametrize("pair", canonical_pairs(), ids=lambda pair: f"{pair['split']}{pair['pair_index']}")
def test_canonical_examples_are_accepted_and_independent_oracle_matches(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert reference_output(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("pattern", ["rectangle", "notched", "split"])
def test_exact_overrides_are_honored_and_pixel_observable(band, pattern):
    requested = {
        "grid_h": 5,
        "grid_w": 10,
        "palette_kind": "cool",
        "pattern_kind": pattern,
    }
    grid = gen.generate(917, 23, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert observed(grid) == requested
    assert gen.observe_overrides(grid) == requested
    assert reference_output(grid) == gen._reference_output(grid)


@pytest.mark.parametrize("key,value", [
    ("typo_axis", 1),
    ("grid_h", True),
    ("grid_h", 4),
    ("grid_h", 9),
    ("grid_w", "12"),
    ("grid_w", 9),
    ("grid_w", 17),
    ("palette_kind", 2),
    ("palette_kind", "unknown"),
    ("pattern_kind", False),
    ("pattern_kind", "unknown"),
])
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, **{key: value})


def test_canonical_shortcuts_really_fit_every_labeled_canonical_pair():
    independent = {
        "fill_hole_bbox": fill_hole_bbox_rival,
        "largest_region_only": largest_region_rival,
        "all_bbox_zeros": all_bbox_zeros_rival,
    }
    for name, rival in independent.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs()), name
        assert all(gen.CANONICAL_SHORTCUTS[name](pair["input"]) == pair["output"]
                   for pair in canonical_pairs()), name


def test_notched_witness_refutes_bbox_and_bbox_zero_shortcuts():
    grid = gen.generate(201, 6, grid_h=5, grid_w=10,
                        palette_kind="canonical", pattern_kind="notched")
    intended = reference_output(grid)
    assert gen.self_check(grid) == []
    assert observed(grid)["pattern_kind"] == "notched"
    assert has_exterior_bbox_zero(grid)
    assert fill_hole_bbox_rival(grid) != intended
    assert all_bbox_zeros_rival(grid) != intended
    assert gen.SEMANTIC_WITNESSES["nonrectangular_hole"](grid)
    assert gen.SEMANTIC_WITNESSES["exterior_bbox_zero"](grid)


def test_split_witness_refutes_largest_region_shortcut():
    grid = gen.generate(202, 7, grid_h=5, grid_w=10,
                        palette_kind="warm", pattern_kind="split")
    intended = reference_output(grid)
    assert gen.self_check(grid) == []
    assert observed(grid)["pattern_kind"] == "split"
    assert any(len(record["regions"]) > 1 for record in object_records(grid))
    assert largest_region_rival(grid) != intended
    assert gen.SEMANTIC_WITNESSES["multiple_hole_regions"](grid)


@pytest.mark.parametrize("start", range(12))
@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_cyclic_start_and_query_rotation_refutes_declared_shortcuts(start, band):
    pairs = make_labeled(gen, seed=7001 + start, start=start, count=5, difficulty=band)
    for query_index in range(len(pairs)):
        query = pairs[query_index]
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(deepcopy(demos), deepcopy(query)) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            fits_demos = all(rival(deepcopy(pair["input"])) == pair["output"] for pair in demos)
            changes_query = rival(deepcopy(query["input"])) != query["output"]
            assert not (fits_demos and changes_query), (start, band, query_index, name)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_covers_profiles_and_is_deterministic(band):
    patterns = set()
    palettes = set()
    profiles = set()
    inputs = set()
    for index in range(96):
        grid = gen.generate(3109 + index, index * 7 + 1, difficulty=band)
        assert grid == gen.generate(3109 + index, index * 7 + 1, difficulty=band)
        assert gen.self_check(grid) == []
        axes = observed(grid)
        patterns.add(axes["pattern_kind"])
        palettes.add(axes["palette_kind"])
        profiles.add((len(grid), len(grid[0]), len({value for row in grid for value in row})))
        inputs.add(digest(grid))
    assert patterns == {"rectangle", "notched", "split"}
    assert palettes == {"canonical", "warm", "cool", "varied"}
    assert profiles & {(5, 12, 3), (6, 12, 3), (6, 14, 3)}
    assert len(inputs) >= 90


@pytest.mark.parametrize("grid", [
    None,
    [],
    [[]],
    [[0], [0, 1]],
    [[True] * 10 for _ in range(5)],
    [[10] * 10 for _ in range(5)],
])
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_validator_rejects_open_frame_and_solid_object_mutations():
    grid = gen.generate(501, 11, grid_h=6, grid_w=12,
                        palette_kind="varied", pattern_kind="rectangle")
    records = object_records(grid)
    r0, c0, r1, c1 = records[0]["bbox"]

    opened = deepcopy(grid)
    opened[r0][(c0 + c1) // 2] = 0
    assert gen.self_check(opened)

    solid = deepcopy(grid)
    color = records[0]["color"]
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            solid[row][col] = color
    assert gen.self_check(solid)


def test_reference_and_rivals_do_not_mutate_inputs():
    grid = gen.generate(77, 8, pattern_kind="split")
    original = deepcopy(grid)
    for solver in [gen._reference_output, *gen.CANONICAL_SHORTCUTS.values()]:
        solver(grid)
        assert grid == original


def test_keyed_generation_is_independent_of_python_hash_seed():
    script = (
        "import importlib.util,json,sys;"
        "p=sys.argv[1];s=importlib.util.spec_from_file_location('g',p);"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "print(json.dumps(m.generate(313,19,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(subprocess.check_output(
            [sys.executable, "-B", "-c", script, str(Path(gen.__file__).resolve())],
            env=env, text=True,
        ))
    assert outputs[0] == outputs[1]
