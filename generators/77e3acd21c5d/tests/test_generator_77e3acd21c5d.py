"""Task-local regression suite for the repaired 77e3acd21c5d generator."""
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
    components8,
    geometry_output,
    load_generator,
    observed,
    profile,
    racket_outputs,
)

GEN = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
CANONICAL_PROFILES = {(20, 24, 6), (22, 20, 5), (20, 20, 6), (28, 28, 8)}


@pytest.mark.parametrize("pair", canonical_pairs(), ids=lambda pair: f"{pair['split']}{pair['pair_index']}")
def test_independent_oracle_matches_every_canonical_label(pair):
    assert geometry_output(pair["input"]) == pair["output"]
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_twenty_default_draws_cover_all_canonical_profiles(band):
    profiles = {
        profile(GEN.generate(9000 + index, index, difficulty=band))
        for index in range(20)
    }
    assert CANONICAL_PROFILES <= profiles


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_has_real_distractors_and_no_fixed_blank(band):
    grids = [GEN.generate(3100 + index, index, difficulty=band) for index in range(40)]
    for grid in grids:
        assert GEN.self_check(grid) == []
        assert len(components8(grid)) >= 3
    stats = [observed(grid) for grid in grids]
    assert len({item["blank_bbox"][:2] for item in stats}) >= 6
    assert len({grid[0][0] for grid in grids}) >= 5
    assert any(item["intended_differs_from_first"] for item in stats)


@pytest.mark.parametrize("profile_name", ["compact4", "stack3", "wide4", "large6"])
@pytest.mark.parametrize("marker_mode", ["corner", "row_tie", "col_tie", "both_tie", "clipped"])
@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_profile_and_marker_mode_overrides_are_exact(profile_name, marker_mode, band):
    grid = GEN.generate(
        17,
        9,
        difficulty=band,
        profile=profile_name,
        marker_mode=marker_mode,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "profile": profile_name,
        "marker_mode": marker_mode,
    }


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_profile": "compact4"},
        {"profile": "not-a-profile"},
        {"marker_mode": "not-a-mode"},
        {"profile": 1},
        {"marker_mode": True},
    ],
)
def test_invalid_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 2, **overrides)


def test_tie_and_clipping_branches_are_real_geometry_witnesses():
    for mode in ("row_tie", "col_tie", "both_tie"):
        grid = GEN.generate(71, 8, profile="large6", marker_mode=mode)
        assert geometry_output(grid) != geometry_output(grid, mirror_ties=False)
        assert GEN.SEMANTIC_WITNESSES["tie_mirroring"](grid)
    clipped = GEN.generate(71, 8, profile="large6", marker_mode="clipped")
    assert GEN.SEMANTIC_WITNESSES["out_of_bounds_filtering"](clipped)


def test_declared_canonical_shortcut_really_fits_canonical_and_is_refuted_generated():
    shortcut = GEN.CANONICAL_SHORTCUTS["single_nearest_anchor"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in canonical_pairs())
    witnesses = [
        GEN.generate(812 + index, index, marker_mode="both_tie")
        for index in range(12)
    ]
    assert all(shortcut(grid) != geometry_output(grid) for grid in witnesses)


def test_widest_source_rival_is_refuted_by_generated_distractors():
    witnesses = [GEN.generate(440 + index, index) for index in range(24)]
    assert sum(
        geometry_output(grid) != geometry_output(grid, selector="first")
        for grid in witnesses
    ) >= 12
    assert any(GEN.SEMANTIC_WITNESSES["widest_source"](grid) for grid in witnesses)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True]]])
def test_malformed_inputs_are_diagnostic_not_exceptions(grid):
    assert GEN.self_check(grid)


def test_generate_is_pure_deterministic_and_hash_seed_independent():
    grid = GEN.generate(991, 23, difficulty="hard")
    frozen = deepcopy(grid)
    assert GEN.generate(991, 23, difficulty="hard") == frozen
    assert GEN.self_check(grid) == []
    assert grid == frozen

    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(991,23,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "98765"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]



def _width_preserving_transform(grid, transform):
    if transform == "identity":
        return deepcopy(grid)
    if transform == "flip_lr":
        return [row[::-1] for row in grid]
    if transform == "flip_ud":
        return [list(row) for row in grid[::-1]]
    if transform == "rot180":
        return [row[::-1] for row in grid[::-1]]
    raise ValueError(transform)


@pytest.mark.parametrize("transform_name", ["identity", "flip_lr", "flip_ud", "rot180"])
def test_rule_geometry_is_equivariant_under_width_preserving_symmetries(transform_name):
    # The authority selects by WIDTH, so quarter-turns are intentionally not
    # symmetries: they exchange width and height and can select another object.
    for index in range(8):
        grid = GEN.generate(700 + index, index, marker_mode="both_tie")
        transformed = _width_preserving_transform(grid, transform_name)
        assert GEN.self_check(transformed) == []
        assert geometry_output(transformed) == _width_preserving_transform(
            geometry_output(grid), transform_name
        )


def test_real_racket_reference_matches_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids.extend(GEN.generate(600 + index, index) for index in range(20))
    assert racket_outputs(grids) == [geometry_output(grid) for grid in grids]


def test_difficulty_bands_change_layout_without_changing_declared_semantics():
    grids = {
        band: GEN.generate(123, 17, difficulty=band)
        for band in ("easy", "medium", "hard")
    }
    assert len({repr(grid) for grid in grids.values()}) == 3
    assert {GEN.observe_overrides(grid)["profile"] for grid in grids.values()} == {"stack3"}
    assert {GEN.observe_overrides(grid)["marker_mode"] for grid in grids.values()} == {"col_tie"}
