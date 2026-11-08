"""Focused regression and semantic-contract tests for fa5bb24054bc."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    CANONICAL_PROFILES,
    area_only_witness,
    canonical_pairs,
    features,
    load_generator,
    observed_axes,
    off_diagonal_codes,
    pair,
    profile,
    relation_output,
    rival_area_equality_means_both,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_pin_and_honest_exact_axes():
    assert gen.RULE_HASH == "b6e6c6e2c73c"
    assert set(gen.AXES) == {"grid_h", "n_panels", "sep_width"}
    assert gen.EXAMPLES_NEEDED == 4
    assert set(gen.SCHEDULE_PROFILES) == {"area_only", "holes_only", "both", "unrelated"}


@pytest.mark.parametrize("pair_data", canonical_pairs(), ids=["train0", "train1", "train2", "train3", "test0"])
def test_canonical_inputs_are_owned_and_independent_oracle_matches(pair_data):
    assert gen.self_check(pair_data["input"]) == []
    assert gen.strict_canonical_like(pair_data["input"]) == []
    assert relation_output(pair_data["input"]) == pair_data["output"]
    assert gen.rule_mirror(pair_data["input"]) == pair_data["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h,n_panels,sep_width", [(3, 2, 1), (3, 6, 2), (8, 2, 2), (8, 6, 1)])
def test_exact_overrides_are_observable_and_fit_arc_limits(band, grid_h, n_panels, sep_width):
    options = {"grid_h": grid_h, "n_panels": n_panels, "sep_width": sep_width}
    grid = gen.generate(917, 13, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed_axes(grid) == options
    assert gen.observe_overrides(grid) == options
    assert len(grid) == grid_h
    assert len(grid[0]) <= 30
    assert grid == gen.generate(917, 13, difficulty=band, **options)


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 1},
        {"grid_h": 2},
        {"grid_h": 9},
        {"n_panels": 1},
        {"n_panels": 7},
        {"sep_width": 0},
        {"sep_width": 3},
        {"grid_h": True},
        {"n_panels": 3.5},
        {"sep_width": "1"},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(overrides):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **overrides)


def test_every_four_sample_window_teaches_all_relation_labels():
    for start in range(16):
        seen = set()
        for sample_index in range(start, start + 4):
            grid = gen.generate(3001, sample_index, grid_h=3, n_panels=2, sep_width=1)
            assert gen.self_check(grid) == []
            seen |= off_diagonal_codes(relation_output(grid))
        assert seen == {0, 2, 3, 6}


def test_canonical_anchor_randomizes_panel_order_without_losing_profile():
    outputs = {
        tuple(tuple(row) for row in relation_output(gen.generate(seed, 0)))
        for seed in range(48)
    }
    assert len(outputs) >= 5


def test_canonical_scale_anchor_is_present_in_every_schedule_octet():
    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(711, index, difficulty=band) for index in range(8)]
        assert any(profile(grid) in CANONICAL_PROFILES for grid in grids)
        assert all(gen.self_check(grid) == [] for grid in grids)


def test_pinned_profile_floor_has_required_canonical_envelope_support():
    exact_total = 0
    envelope_total = 0
    per_band_exact = {}
    for band in ("easy", "medium", "hard"):
        band_exact = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:fa5bb24054bc:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
            h, w, palette = profile(grid)
            is_exact = (h, w, palette) in CANONICAL_PROFILES
            band_exact += is_exact
            exact_total += is_exact
            envelope_total += 3 <= h <= 4 and 10 <= w <= 12 and palette == 4
        per_band_exact[band] = band_exact
    assert all(count >= 1 for count in per_band_exact.values())
    assert exact_total >= 1
    assert envelope_total >= 15


def test_every_declared_semantic_witness_has_an_explicit_rival_claim():
    assert set(gen.SEMANTIC_WITNESSES) == set(gen.WITNESS_RIVALS)
    assert all(gen.WITNESS_RIVALS[name] for name in gen.SEMANTIC_WITNESSES)


def test_area_only_witness_refutes_the_canonical_shortcut():
    grid = area_only_witness()
    assert features(grid) == [(8, 0), (8, 1)]
    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid) == [[5, 2], [2, 5]]
    assert rival_area_equality_means_both(grid) == [[5, 6], [6, 5]]
    assert gen.SEMANTIC_WITNESSES["same_area_different_holes"](grid)
    assert gen.SEMANTIC_RIVALS["same_area_means_both"](grid) != gen.rule_mirror(grid)
    assert "same_area_means_both" in gen.WITNESS_RIVALS["same_area_different_holes"]


def test_declared_area_shortcuts_fit_every_canonical_pair_but_not_witness():
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(p["input"]) == p["output"] for p in canonical_pairs()), name
        assert rival(area_only_witness()) != relation_output(area_only_witness()), name


def test_four_demo_lesson_is_identifiable_against_declared_rivals():
    demos = [pair(gen, 404, index, grid_h=3, n_panels=2, sep_width=1) for index in range(4)]
    query = pair(gen, 404, 4, grid_h=3, n_panels=2, sep_width=1)
    assert gen.lesson_identifiable(demos, query) == []

    missing_area_only = [demos[1], demos[2], demos[3], deepcopy(demos[1])]
    reasons = gen.lesson_identifiable(missing_area_only, query)
    assert any("label 2" in reason or "same-area" in reason for reason in reasons)


def test_task_local_qualifier_checks_cyclic_windows_and_joint_axes():
    from qualify import audit

    report = audit(gen, per_band=8, window_starts=8)
    assert report["cyclic_window_failures"] == []
    assert report["joint_override_failures"] == []
    assert report["joint_override_cases"] == 60
    assert report["max_generated_width"] <= 30
    assert set(report["canonical_fitting_shortcuts"]) == {
        "same_area_means_both",
        "no_area_only_relation",
    }
    assert all(count > 0 for count in report["generated_shortcut_refutations"].values())
    assert all(
        0 <= stats.get("canonical_profile", 0) <= stats["samples"]
        for stats in report["by_band"].values()
    )


def test_rule_mirror_and_validator_do_not_mutate_inputs():
    grid = gen.generate(93, 7, difficulty="hard")
    before = deepcopy(grid)
    assert gen.rule_mirror(grid)
    assert gen.self_check(grid) == []
    assert grid == before


@pytest.mark.parametrize("name", ["no_separators", "single_panel", "multicolor_panel", "disconnected_panel"])
def test_negative_fixtures_are_rejected(name):
    grid = gen.make_degenerate(name)
    assert gen.self_check(grid), name


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True, 0], [0, 0]], [[10, 0], [0, 0]]])
def test_malformed_grids_return_diagnostics_instead_of_raising(bad):
    assert gen.self_check(bad)
