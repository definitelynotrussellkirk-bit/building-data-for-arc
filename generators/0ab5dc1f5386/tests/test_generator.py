"""Task-local regression and semantic curriculum tests for 0ab5dc1f5386."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (canonical, canonical_pairs, flatten_shape_output,
                             intended_output, last_match_output, load_generator,
                             loose_crops, normalized_rule_hash, observed_profile,
                             occurrence_use_output, racket_outputs, reuse_shape_output,
                             rotate_to_fit_output)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
CANONICAL_PROFILES = {(12, 16, 5), (13, 17, 5), (13, 18, 5)}
TEXTURES = ("orientation_decoy", "scan_order", "single_use", "multicolor", "unmatched")


def test_rule_pin_authority_sync_and_canonical_acceptance():
    row = canonical()
    assert gen.RULE_HASH == normalized_rule_hash(row["program_solution"])
    authority = json.loads((HOME.parents[1] / "shared/data/base/solutions/banks/868e1a8cbe17/H125__0ab5dc1f5386.json").read_text())
    assert authority["racket_target"]["target_code"] == row["program_solution"]
    for pair in canonical_pairs():
        assert gen.self_check(pair["input"]) == []
        assert intended_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("texture", TEXTURES)
def test_exact_boundary_overrides_are_honored_in_every_band(band, texture):
    for h, w in ((12, 16), (18, 22)):
        grid = gen.generate(31, 7, difficulty=band, grid_h=h, grid_w=w, texture=texture)
        assert gen.self_check(grid) == []
        assert (len(grid), len(grid[0])) == (h, w)
        assert gen.observe_overrides(grid) == {"grid_h": h, "grid_w": w}
        assert len({v for row in grid for v in row}) == 5
        assert intended_output(grid) != grid


@pytest.mark.parametrize("overrides", [
    {"typo": 1}, {"grid_h": 11}, {"grid_h": 19}, {"grid_w": 15},
    {"grid_w": 23}, {"grid_h": True}, {"grid_w": 16.5},
    {"texture": "no_frames"}, {"texture": 3},
])
def test_invalid_overrides_are_rejected(overrides):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_lawful_deterministic_and_canonical_scaled(band):
    seen = set()
    profiles = set()
    corner_free = 0
    densities = set()
    for index in range(96):
        grid = gen.generate(700 + index, index, difficulty=band)
        assert grid == gen.generate(700 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert intended_output(grid) != grid
        profile = observed_profile(grid)
        assert profile in CANONICAL_PROFILES
        profiles.add(profile)
        seen.add(json.dumps(grid, separators=(",", ":")))
        for crop in loose_crops(grid):
            nonzero = sum(value != 0 for row in crop for value in row)
            densities.add((nonzero, len(crop) * len(crop[0])))
            corner_free += crop[0][0] == 0 or crop[-1][-1] == 0
    assert profiles == CANONICAL_PROFILES
    assert len(seen) >= 90
    assert corner_free > 20
    assert len(densities) >= 8


def test_declared_canonical_shortcuts_really_fit_every_canonical_pair():
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "rotate_to_fit", "last_match", "flatten_shape", "occurrence_use"
    }
    for pair in canonical_pairs():
        for name, rival in gen.CANONICAL_SHORTCUTS.items():
            assert rival(pair["input"]) == pair["output"], name


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_cyclic_four_demo_window_refutes_every_lesson_competitor(band):
    assert set(gen.LESSON_COMPETITORS) == {
        "rotate_to_fit", "last_match", "reuse_shape", "flatten_shape",
        "occurrence_use",
    }
    # The default schedule has period four; check every cyclic starting offset.
    for start in range(4):
        demos = [gen.generate(911, start + offset, difficulty=band) for offset in range(4)]
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(grid) != intended_output(grid) for grid in demos), (start, name)


def test_each_scheduled_profile_is_an_exact_named_counterexample():
    expected = {
        "orientation_decoy": ("rotate_to_fit",),
        "scan_order": ("last_match",),
        "single_use": ("reuse_shape", "occurrence_use"),
        "multicolor": ("flatten_shape",),
    }
    rivals = dict(gen.SEMANTIC_RIVALS)
    for index, texture in enumerate(gen.SCHEDULE_PROFILES):
        grid = gen.generate(1201, index)
        assert gen.schedule_profile(1201, index) == texture
        assert gen.SEMANTIC_WITNESSES[texture](grid)
        for rival_name in expected[texture]:
            assert rivals[rival_name](grid) != intended_output(grid)


def test_single_use_profile_teaches_value_equality_not_occurrence_identity():
    grid = gen.generate(1201, 2)
    crops = loose_crops(grid)
    assert len(crops) == 2
    assert crops[0] == crops[1]
    assert occurrence_use_output(grid) != intended_output(grid)
    assert gen.SEMANTIC_RIVALS["occurrence_use"](grid) == occurrence_use_output(grid)


def test_independent_rivals_agree_with_declared_rivals_on_witnesses():
    independent = {
        "rotate_to_fit": rotate_to_fit_output,
        "last_match": last_match_output,
        "flatten_shape": flatten_shape_output,
        "reuse_shape": reuse_shape_output,
        "occurrence_use": occurrence_use_output,
    }
    for index, texture in enumerate(gen.SCHEDULE_PROFILES):
        grid = gen.generate(2121, index)
        for name, oracle in independent.items():
            assert gen.SEMANTIC_RIVALS[name](grid) == oracle(grid)


def test_real_racket_matches_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status
    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(4400 + i, i, difficulty=("easy", "medium", "hard")[i % 3]) for i in range(24)]
    assert racket_outputs(grids) == [intended_output(grid) for grid in grids]


def test_hashseed_does_not_change_default_pixels():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(51,13,difficulty='hard')))"
    )
    outputs = []
    for hashseed in ("1", "90210"):
        env = dict(os.environ, PYTHONHASHSEED=hashseed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(subprocess.check_output(
            [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
            env=env, text=True,
        ))
    assert outputs[0] == outputs[1]
