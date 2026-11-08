"""Test-first repair contract for ARC generator 0701a2c36d45."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import os
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared" / "runtime"))
sys.path.insert(0, str(HOME / "workspace"))

from reviewer_support import canonical_pairs
from review_probe import load_generator, palette_size, vote_profile

GEN = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
CANONICAL = canonical_pairs("0701a2c36d45", root=ROOT, labeled_only=True)


def label(grid):
    return {"input": deepcopy(grid), "output": GEN._rule_mirror(grid)}


def test_metadata_exposes_only_truthful_lawful_axes():
    assert GEN.RULE_HASH == "606946fe96ab"
    assert set(GEN.AXES) == {"panel_h", "panel_w", "shape_size", "texture"}
    assert GEN.AXES["texture"]["valid"] == "plain|two_agree|noise_robust|mixed_vote"
    assert "n_panels" not in GEN.AXES


@pytest.mark.parametrize("pair", CANONICAL,
                         ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_canonical_examples_are_accepted_and_mirrored(pair):
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert GEN._rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("options", [
    {"panel_h": 3, "panel_w": 3, "shape_size": 8, "texture": "two_agree"},
    {"panel_h": 8, "panel_w": 3, "shape_size": 2, "texture": "noise_robust"},
    {"panel_h": 4, "panel_w": 8, "shape_size": 5, "texture": "plain"},
    {"panel_h": 3, "panel_w": 3, "shape_size": 8, "texture": "mixed_vote"},
])
def test_exact_overrides_are_realized_in_every_band(band, options):
    grid = GEN.generate(817, 29, difficulty=band, **options)
    assert GEN.self_check(grid) == []
    observed = vote_profile(grid)
    assert {name: observed[name] for name in options} == options
    assert GEN.observe_overrides(grid) == options


@pytest.mark.parametrize("key,value", [
    ("typo", 1),
    ("panel_h", 2), ("panel_h", 9), ("panel_h", True), ("panel_h", 4.0),
    ("panel_w", "4"),
    ("shape_size", 1), ("shape_size", 9), ("shape_size", False),
    ("texture", "no_header"), ("texture", "mismatched_codes"),
])
def test_invalid_or_degenerate_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **{key: value})


def test_default_schedule_is_rotation_safe_and_covers_all_semantic_profiles():
    for band in (None, "easy", "medium", "hard"):
        for start in range(18):
            five = []
            for index in range(start, start + 5):
                grid = GEN.generate(431, index, difficulty=band)
                profile = vote_profile(grid)["texture"]
                assert profile == GEN.schedule_profile(431, index, difficulty=band)
                five.append(profile)
            assert five.count("mixed_vote") >= 2
        six = {
            vote_profile(GEN.generate(431, index, difficulty=band))["texture"]
            for index in range(6)
        }
        assert six == {"plain", "noise_robust", "two_agree", "mixed_vote"}


@pytest.mark.parametrize("texture", ["plain", "noise_robust", "two_agree", "mixed_vote"])
def test_vote_textures_have_the_promised_majority_semantics(texture):
    grid = GEN.generate(1337, 5, panel_h=4, panel_w=4,
                        shape_size=5, texture=texture)
    observed = vote_profile(grid)
    assert observed["texture"] == texture
    assert observed["output"] == GEN._rule_mirror(grid)
    if texture == "plain":
        assert not observed["count1"] and not observed["count2"]
        assert observed["panel_sizes"] == (5, 5, 5)
    elif texture == "noise_robust":
        assert len(observed["count1"]) == 1 and not observed["count2"]
        assert observed["panel_sizes"] == (5, 5, 6)
        assert sum(value == 8 for row in observed["output"] for value in row) == 5
    elif texture == "two_agree":
        assert not observed["count1"] and len(observed["count2"]) == 1
        assert observed["panel_sizes"] == (5, 6, 6)
        assert sum(value == 8 for row in observed["output"] for value in row) == 6
    else:
        assert len(observed["count1"]) == 1 and len(observed["count2"]) == 1
        assert observed["panel_sizes"] == (5, 5, 5)
        assert sum(value == 8 for row in observed["output"] for value in row) == 5


def test_validator_rejects_destructive_structural_and_semantic_mutations():
    original = GEN.generate(91, 2, panel_h=4, panel_w=4,
                            shape_size=4, texture="plain")
    mutations = []

    bad_header = deepcopy(original)
    bad_header[0][0] = 0
    mutations.append(bad_header)

    broken_separator = deepcopy(original)
    broken_separator[1][0] = 0
    mutations.append(broken_separator)

    blank_panel = deepcopy(original)
    for r in range(2, 6):
        blank_panel[r] = [0] * 4
    mutations.append(blank_panel)

    partial_nine = deepcopy(original)
    partial_nine[2][3] = 9
    mutations.append(partial_nine)

    multi_noise = deepcopy(original)
    # Add unrelated cells to two raw panels; this is not one of the three
    # declared vote profiles even if both additions survive normalization.
    color0 = next(v for row in multi_noise[2:6] for v in row if v not in (0, 9))
    color1 = next(v for row in multi_noise[7:11] for v in row if v not in (0, 9))
    zero0 = next((r, c) for r in range(2, 6) for c in range(4) if multi_noise[r][c] == 0)
    zero1 = next((r, c) for r in range(7, 11) for c in range(4) if multi_noise[r][c] == 0)
    multi_noise[zero0[0]][zero0[1]] = color0
    multi_noise[zero1[0]][zero1[1]] = color1
    mutations.append(multi_noise)

    for grid in mutations:
        assert GEN.self_check(grid), grid


def test_canonical_profile_has_support_in_every_band_and_exceeds_floor():
    for band in ("easy", "medium", "hard"):
        matches = 0
        for i in range(40):
            grid = GEN.generate(7000 + i, i * 11, difficulty=band)
            if (len(grid), len(grid[0]), palette_size(grid)) == (16, 4, 6):
                matches += 1
        assert matches >= 10, (band, matches)


def test_declared_rivals_fit_where_claimed_and_every_scheduled_lesson_refutes_them():
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in CANONICAL), name

    for band in ("easy", "medium", "hard"):
        for start in range(0, 44, 4):
            lesson = [label(GEN.generate(223, start + i, difficulty=band)) for i in range(5)]
            for held_out in range(5):
                demos = [pair for i, pair in enumerate(lesson) if i != held_out]
                query = lesson[held_out]
                assert GEN.lesson_identifiable(demos, query) == []
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_witnesses_are_real_counterexamples_to_their_declared_rivals():
    pooled = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    for index in range(24):
        grid = GEN.generate(551, index)
        truth = GEN._rule_mirror(grid)
        for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
            if witness(grid):
                pooled[witness_name] += 1
                assert any(
                    GEN.SEMANTIC_RIVALS[rival](grid) != truth
                    for rival in GEN.WITNESS_RIVALS[witness_name]
                )
    assert all(count > 0 for count in pooled.values()), pooled


def test_exhaustive_cyclic_probe_covers_every_schedule_residue():
    from cyclic_lesson_probe import audit_windows

    report = audit_windows(
        generator=GEN,
        seed=223,
        bands=("easy", "medium", "hard"),
        period=6,
        window=5,
    )
    assert report["summary"] == {
        "bands": 3,
        "starts": 18,
        "rotations": 90,
        "ambiguous_rotations": 0,
        "hook_failures": 0,
    }
    for band in ("easy", "medium", "hard"):
        assert {row["start"] for row in report["windows"] if row["band"] == band} == set(range(6))
