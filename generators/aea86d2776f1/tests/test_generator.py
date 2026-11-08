"""Task-local regression tests for aea86d2776f1."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    alternating_sources_rival,
    canonical,
    canonical_pairs,
    cropped_templates_rival,
    intended_output,
    load_generator,
    monochrome_templates_rival,
    observed,
    racket_outputs,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=lambda p: hashlib.sha1(json.dumps(p["input"]).encode()).hexdigest()[:8])
def test_canonical_inputs_are_accepted_and_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]


def test_rule_hash_is_pinned_to_selected_authority():
    normalized = " ".join(canonical()["program_solution"].split())
    expected = hashlib.sha256(normalized.encode()).hexdigest()[:12]
    assert gen.RULE_HASH == expected == "5d25ec4af105"


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_exact_override_is_observable_in_every_band(band):
    requested = {
        "left_cells": 8,
        "right_cells": 3,
        "left_colors": 3,
        "right_colors": 2,
        "source_balance": 1,
        "transform_count": 2,
    }
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert observed(grid) == requested
    assert grid == gen.generate(17, 9, difficulty=band, **requested)
    assert (len(grid), len(grid[0])) == (5, 11)


@pytest.mark.parametrize("key,value", [
    ("typo", 1),
    ("left_cells", 2), ("left_cells", 9),
    ("right_cells", 2), ("right_cells", 9),
    ("left_colors", 0), ("left_colors", 4),
    ("right_colors", 0), ("right_colors", 4),
    ("source_balance", 0), ("source_balance", 4),
    ("transform_count", 1), ("transform_count", 5),
    ("left_cells", 4.5), ("right_colors", True),
])
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


def test_declared_schedule_repeats_four_profiles():
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "canonical_core",
        "multicolor_left",
        "multicolor_right",
        "dense_counterexample",
    )
    assert [gen.schedule_profile(3, index, "hard") for index in range(8)] == list(gen.SCHEDULE_PROFILES) * 2


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_four_pair_window_retains_rotated_lesson_witnesses(band):
    grids = [gen.generate(700 + index, index, difficulty=band) for index in range(12)]
    for index, grid in enumerate(grids):
        assert gen.self_check(grid) == []
        assert grid == gen.generate(700 + index, index, difficulty=band)
        assert (len(grid), len(grid[0])) == (5, 11)

    for start in range(9):
        window = grids[start:start + 4]
        profiles = {gen.schedule_profile(700 + start + offset, start + offset, band) for offset in range(4)}
        assert profiles == set(gen.SCHEDULE_PROFILES)
        canonical_profiles = [
            grid for grid in window
            if observed(grid) == {
                "left_cells": 5,
                "right_cells": 5,
                "left_colors": 1,
                "right_colors": 1,
                "source_balance": 2,
                "transform_count": 4,
            }
        ]
        assert canonical_profiles
        for name, rival in gen.LESSON_COMPETITORS.items():
            disagreements = sum(rival(grid) != intended_output(grid) for grid in window)
            assert disagreements >= 2, (start, name, disagreements)


def test_canonical_shortcuts_really_fit_all_canonical_pairs():
    independent = {
        "alternating_sources": alternating_sources_rival,
        "monochrome_templates": monochrome_templates_rival,
        "cropped_templates": cropped_templates_rival,
    }
    assert set(gen.CANONICAL_SHORTCUTS) == set(independent)
    assert set(gen.LESSON_COMPETITORS) == set(independent)
    for pair in canonical_pairs():
        for name, rival in independent.items():
            assert rival(pair["input"]) == pair["output"], name
            assert gen.CANONICAL_SHORTCUTS[name](pair["input"]) == pair["output"], name


@pytest.mark.parametrize("profile,rival", [
    ("multicolor_left", "monochrome_templates"),
    ("multicolor_right", "cropped_templates"),
    ("dense_counterexample", "alternating_sources"),
])
def test_named_profiles_are_real_counterexamples(profile, rival):
    index = list(gen.SCHEDULE_PROFILES).index(profile)
    grid = gen.generate(918, index, difficulty="hard")
    assert gen.schedule_profile(918, index, "hard") == profile
    assert gen.SEMANTIC_RIVALS[rival](grid) != intended_output(grid)
    witnesses = [name for name, rivals in gen.WITNESS_RIVALS.items() if rival in rivals]
    assert witnesses and any(gen.SEMANTIC_WITNESSES[name](grid) for name in witnesses)


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True] * 11 for _ in range(5)]])
def test_malformed_inputs_are_diagnostic_not_exceptions(bad):
    assert gen.self_check(bad)


def test_self_check_rejects_nonblank_outside_fixed_regions():
    grid = gen.generate(31, 6)
    changed = deepcopy(grid)
    changed[1][5] = 9
    assert any("outside" in item for item in gen.self_check(changed))


def test_real_racket_matches_independent_oracle():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(f"protected Racket runtime unavailable in direct test process: {status['reason']}")
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(404 + index, index, difficulty=("easy", "medium", "hard")[index % 3]) for index in range(12)]
    assert racket_outputs(grids) == [intended_output(grid) for grid in grids]


def test_default_schedule_does_not_lock_right_colors_to_source_balance():
    rows = [observed(gen.generate(1234 + index, index, difficulty="medium")) for index in range(4)]
    balances_when_right_is_monochrome = {
        row["source_balance"] for row in rows if row["right_colors"] == 1
    }
    assert len(balances_when_right_is_monochrome) >= 2


def test_difficulty_bands_change_pixels_without_changing_declared_axes():
    grids = {
        band: gen.generate(2468, 7, difficulty=band)
        for band in ("easy", "medium", "hard")
    }
    assert len({json.dumps(grid) for grid in grids.values()}) == 3
    assert len({tuple(observed(grid).items()) for grid in grids.values()}) == 1
