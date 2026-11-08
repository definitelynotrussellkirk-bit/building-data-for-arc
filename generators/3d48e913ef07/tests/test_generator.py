"""Task-local regressions for the area-ranked palette packing generator."""
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
from reference_probe import (  # noqa: E402
    bbox,
    canonical_pairs,
    components,
    load_generator,
    object_signature,
    observed,
    packed_output,
    palette,
    racket_outputs,
    shortcut_witness,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_hash_is_pinned_to_current_authority():
    assert gen.RULE_HASH == "4d5171afc86a"


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "train2", "test0"])
def test_canonical_pairs_match_independent_oracle_and_validator(pair):
    assert packed_output(pair["input"]) == pair["output"]
    assert gen.self_check(pair["input"]) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 10, "grid_w": 14, "n_objs": 5},
        {"grid_h": 18, "grid_w": 20, "n_objs": 3},
    ],
)
def test_exact_override_domain_is_constructive_in_every_band(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo_axis", 1),
        ("grid_h", 9),
        ("grid_h", 19),
        ("grid_w", 13),
        ("grid_w", 21),
        ("n_objs", 2),
        ("n_objs", 6),
        ("grid_h", True),
        ("grid_w", 14.0),
        ("n_objs", "3"),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


def test_all_advertised_multi_axis_combinations_are_exact_and_deterministic():
    for band in (None, "easy", "medium", "hard"):
        for h in range(10, 19):
            for w in range(14, 21):
                for n in range(3, 6):
                    options = {"grid_h": h, "grid_w": w, "n_objs": n}
                    grid = gen.generate(901 + h, 100 * n + w, difficulty=band, **options)
                    assert grid == gen.generate(901 + h, 100 * n + w, difficulty=band, **options)
                    assert gen.self_check(grid) == []
                    assert observed(grid) == options


def test_shortcut_witness_separates_all_declared_semantics():
    grid = shortcut_witness()
    intended = packed_output(grid)
    expected = {
        "source_order": packed_output(grid, object_order="source"),
        "ascending_area": packed_output(grid, object_order="ascending_area"),
        "bbox_area": packed_output(grid, object_order="bbox_area"),
        "bbox_width": packed_output(grid, object_order="bbox_width"),
        "numeric_palette": packed_output(grid, palette_order="numeric"),
    }
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    for name, rival in expected.items():
        assert rival != intended, name
        assert gen.SEMANTIC_WITNESSES[name](grid), name
        assert gen.SEMANTIC_RIVALS[name](grid) == rival, name
        assert gen.LESSON_COMPETITORS[name](grid) == rival, name
        assert name in gen.WITNESS_RIVALS[name]

    # Bbox width is the strongest public-data ambiguity found in this review:
    # it fits all four pairs.  Every other named rival is already public-falsified.
    assert set(gen.CANONICAL_SHORTCUTS) == {"bbox_width"}
    assert all(
        gen.CANONICAL_SHORTCUTS["bbox_width"](pair["input"]) == pair["output"]
        for pair in canonical_pairs()
    )
    for name, rival in gen.SEMANTIC_RIVALS.items():
        if name != "bbox_width":
            assert any(rival(pair["input"]) != pair["output"] for pair in canonical_pairs()), name


@pytest.mark.parametrize(
    "mutation",
    ["missing_palette", "duplicate_palette", "foreign_color", "reserved_column", "equal_object_areas"],
)
def test_validator_rejects_semantically_broken_mutations(mutation):
    grid = shortcut_witness()
    if mutation == "missing_palette":
        grid[8][0] = 0
    elif mutation == "duplicate_palette":
        grid[8][0] = grid[4][0]
    elif mutation == "foreign_color":
        grid[0][5] = 8
    elif mutation == "reserved_column":
        grid[5][1] = 3
    elif mutation == "equal_object_areas":
        # Compact area-6 rectangle becomes a connected area-5 object, tying the plus.
        grid[7][5] = 0
    assert gen.self_check(grid)


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True] * 14 for _ in range(10)]])
def test_malformed_grids_return_diagnostics_not_exceptions(bad):
    assert gen.self_check(bad)


def test_generated_curriculum_breaks_source_and_numeric_palette_shortcuts():
    canonical_dims = {(10, 14), (10, 15), (11, 15), (12, 14)}
    for band in (None, "easy", "medium", "hard"):
        exact_profile_hits = 0
        source_counterexamples = 0
        palette_counterexamples = 0
        width_counterexamples = 0
        inputs = set()
        signatures = set()
        for index in range(96):
            grid = gen.generate(2000 + index, index * 13 + 1, difficulty=band)
            assert gen.self_check(grid) == []
            assert grid == gen.generate(2000 + index, index * 13 + 1, difficulty=band)
            exact_profile_hits += (len(grid), len(grid[0])) in canonical_dims
            source_counterexamples += packed_output(grid) != packed_output(grid, object_order="source")
            palette_counterexamples += packed_output(grid) != packed_output(grid, palette_order="numeric")
            width_counterexamples += packed_output(grid) != packed_output(grid, object_order="bbox_width")
            inputs.add(str(grid))
            signatures.add(object_signature(grid))
        assert exact_profile_hits > 0
        assert source_counterexamples == 96
        assert palette_counterexamples == 96
        assert width_counterexamples == 96
        assert len(inputs) >= 90
        assert len(signatures) >= 12


def test_independent_oracle_matches_real_racket_authority():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()] + [shortcut_witness()]
    grids += [gen.generate(4300 + i, i * 5, difficulty=("easy", "medium", "hard")[i % 3]) for i in range(24)]
    originals = deepcopy(grids)
    outputs = racket_outputs(grids)
    assert grids == originals
    assert outputs == [packed_output(grid) for grid in grids]


def test_generator_does_not_touch_global_random_state():
    random.seed(123456)
    before = random.getstate()
    gen.generate(77, 11, difficulty="hard")
    assert random.getstate() == before


def test_python_hash_seed_does_not_change_pixels():
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
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")], env=env, text=True
            )
        )
    assert results[0] == results[1]
