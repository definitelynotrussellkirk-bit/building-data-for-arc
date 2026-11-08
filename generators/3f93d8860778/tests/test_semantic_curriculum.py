"""Regressions for the v4 lesson-level semantic repair."""
from __future__ import annotations

import copy
import importlib
from collections import Counter

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "3f93d8860778"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _guard_kinds(grid) -> Counter:
    return Counter(decoy["kind"] for decoy in GEN._analysis(grid)["decoys"])


def _pair_colour_repeated(grid) -> bool:
    colours = GEN._analysis(grid)["colours"]
    return len(set(colours)) < len(colours)


CANONICAL_PROFILES = {
    (7, 11, 4),
    (8, 10, 4),
    (9, 8, 4),
    (10, 9, 4),
    (12, 8, 4),
}


def _profile(grid):
    return (len(grid), len(grid[0]), len({value for row in grid for value in row}))


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_canonical_anchor_covers_all_schedule_profiles(band):
    # Indices 0, 5, and 10 are all anchor slots and cover residues 0, 2, 1 mod 3.
    grids = [GEN.generate(123456, index, difficulty=band) for index in (0, 5, 10)]
    assert {_profile(grid) for grid in grids} <= CANONICAL_PROFILES
    assert {GEN.schedule_profile(123456, index, band) for index in (0, 5, 10)} == set(
        GEN.SCHEDULE_PROFILES
    )
    for index, grid in zip((0, 5, 10), grids):
        if GEN.schedule_profile(123456, index, band) != "canonical_clean":
            colours = GEN._analysis(grid)["colours"]
            assert 1 < len(set(colours)) < len(colours)


def test_unknown_override_is_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=9)


def test_frozen_fixture_is_still_byte_identical_to_baseline():
    fixture = find_root(__file__) / "generators" / TASK_ID / "tests" / f"test_generator_{TASK_ID}.py"
    # This digest is the packet baseline.  New tests belong in this module.
    import hashlib
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == (
        "c9e4a1e6ebb1873156bf79a6357b9123a8dee23ce609114f9cd9ee70b3e489f6"
    )


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_period_three_schedule_has_exact_clean_and_guard_signatures(band):
    complete_guard = Counter({
        "mismatched_pair": 1,
        "singleton": 1,
        "same_colour_triple": 1,
    })
    expected = [Counter(), complete_guard, complete_guard]
    assert GEN.SCHEDULE_PROFILES == (
        "canonical_clean",
        "mismatched_guard",
        "multiplicity_guard",
    )
    for start in range(3):
        profiles = []
        for offset in range(3):
            index = start + offset
            grid = GEN.generate(616161, index, difficulty=band)
            assert GEN.self_check(grid) == []
            profiles.append(GEN.schedule_profile(616161, index, band))
            signature = expected[index % 3]
            assert _guard_kinds(grid) == signature
            assert _pair_colour_repeated(grid) is bool(signature)
        assert set(profiles) == set(GEN.SCHEDULE_PROFILES)


@pytest.mark.parametrize("profile_index", [1, 2])
def test_guard_columns_are_left_unchanged_while_valid_pairs_fill(profile_index):
    grid = GEN.generate(44004, profile_index, difficulty="medium")
    out = GEN.rule_mirror(grid)
    info = GEN._analysis(grid)
    for decoy in info["decoys"]:
        column = decoy["column"]
        assert [row[column] for row in out] == [row[column] for row in grid]
    for pair in info["pairs"]:
        assert all(
            out[row][pair["column"]] == pair["colour"]
            for row in range(pair["top"], pair["bottom"] + 1)
        )


def test_partial_guard_signatures_remain_invalid():
    clean = GEN.generate(333, 0, difficulty="medium")
    pairs = GEN._analysis(clean)["pairs"]
    first, second = pairs[:2]

    singleton_only = copy.deepcopy(clean)
    singleton_only[first["bottom"]][first["column"]] = 0
    assert GEN.self_check(singleton_only)

    mismatch_only = copy.deepcopy(clean)
    mismatch_only[first["bottom"]][first["column"]] = first["colour"] % 9 + 1
    assert GEN.self_check(mismatch_only)

    repeated_pair_colour_only = copy.deepcopy(clean)
    for row in (second["top"], second["bottom"]):
        repeated_pair_colour_only[row][second["column"]] = first["colour"]
    assert GEN.self_check(repeated_pair_colour_only)


@pytest.mark.parametrize("name", [
    "fill_every_active_column",
    "fill_matching_extrema",
    "global_exact_two_colours",
    "fill_singletons_to_bottom",
])
def test_new_public_shortcut_fits_canonical_but_loses_on_every_schedule_window(name):
    assert name in GEN.SEMANTIC_RIVALS
    assert name in GEN.CANONICAL_SHORTCUTS
    assert name in GEN.LESSON_COMPETITORS
    rival = GEN.CANONICAL_SHORTCUTS[name]
    assert all(rival(pair["input"]) == pair["output"] for pair in _canonical_pairs())

    for band in ("easy", "medium", "hard"):
        for start in range(3):
            demos = []
            for index in range(start, start + GEN.EXAMPLES_NEEDED):
                grid = GEN.generate(8080, index, difficulty=band)
                demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
            assert any(
                GEN.LESSON_COMPETITORS[name](pair["input"]) != pair["output"]
                for pair in demos
            ), (name, band, start)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_cyclic_lesson_start_is_identifiable(band):
    for start in range(3):
        pairs = []
        for index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
            grid = GEN.generate(9191, index, difficulty=band)
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        assert GEN.lesson_identifiable(pairs[:-1], pairs[-1]) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_query_rotation_of_four_consecutive_pairs_is_identifiable(band):
    for start in range(3):
        pairs = []
        for index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
            grid = GEN.generate(272727, index, difficulty=band)
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, query) == [], (
                band, start, query_index
            )


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_default_guard_has_repeated_and_distinct_pair_colours(band):
    for index in range(60):
        if GEN.schedule_profile(515151, index, band) == "canonical_clean":
            continue
        grid = GEN.generate(515151, index, difficulty=band)
        colours = GEN._analysis(grid)["colours"]
        assert len(colours) >= 3
        assert 1 < len(set(colours)) < len(colours)


def test_source_bound_shortcut_probe_uses_public_declarations(tmp_path):
    import json
    import subprocess
    import sys
    from pathlib import Path

    script = Path(__file__).resolve().parents[1] / "workspace" / "shortcut_probe.py"
    out = tmp_path / "probe.json"
    run = subprocess.run(
        [sys.executable, str(script), "--per-band", "6", "--out", str(out)],
        check=False,
        text=True,
        capture_output=True,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    report = json.loads(out.read_text())
    assert report["status"] == "pass"
    assert set(report["declarations"]) == {
        "CANONICAL_SHORTCUTS",
        "LESSON_COMPETITORS",
        "SEMANTIC_RIVALS",
    }
    assert all(report["canonical_rival_fit"].values())
    assert report["cyclic_rotations"]["failures"] == []
