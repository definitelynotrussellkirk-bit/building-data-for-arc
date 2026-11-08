"""Focused contract and shortcut regressions for 9b5d72b45563."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import random

import pytest
from reviewer_support import canonical_pairs, find_root


TASK_ID = "9b5d72b45563"
TASK_HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", TASK_HOME / "generator.py"))


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def _seed_cells(grid):
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]


def _palette_profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_rule_hash_and_single_exact_axis_contract_are_pinned():
    assert gen.RULE_HASH == "cc30c7127a64"
    assert set(gen.AXES) == {"scene_profile"}
    assert tuple(gen.AXES["scene_profile"]["valid"].split("|")) == tuple(gen.SCENE_PROFILES)
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


def test_canonical_inputs_are_accepted_and_python_mirror_matches_every_label():
    assert len(PAIRS) == 4
    for pair in PAIRS:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_declared_canonical_shortcuts_really_fit_all_canonical_pairs():
    assert {
        "first_two_seeds_only",
        "right_to_left_within_rows",
        "first_seed_per_color",
    } <= set(gen.CANONICAL_SHORTCUTS)
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in PAIRS), name


def test_same_row_overlap_uses_left_to_right_last_writer_precedence():
    grid = [[0] * 7 for _ in range(7)]
    grid[3][2] = 2
    grid[3][4] = 7
    assert gen.self_check(grid) == []

    intended = gen.rule_mirror(grid)
    reverse = gen.CANONICAL_SHORTCUTS["right_to_left_within_rows"](grid)
    assert intended[2][3] == intended[4][3] == 7
    assert reverse[2][3] == reverse[4][3] == 2
    assert intended != reverse


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_profile_override_is_exact_observable_and_valid_in_every_band(band):
    for index, profile in enumerate(gen.SCENE_PROFILES):
        grid = gen.generate(
            1000 + index,
            2000 + index,
            difficulty=band,
            scene_profile=profile,
        )
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == {"scene_profile": profile}
        assert (len(grid), len(grid[0])) == gen.SCENE_SPECS[profile]["size"]


def test_every_teaching_profile_refutes_every_canonical_shortcut():
    for index, profile in enumerate(gen.TEACHING_PROFILES):
        grid = gen.generate(7000 + index, index, scene_profile=profile)
        intended = gen.rule_mirror(grid)
        assert len(_seed_cells(grid)) >= 3
        for name, rival in gen.CANONICAL_SHORTCUTS.items():
            assert rival(grid) != intended, (profile, name)


def test_every_cyclic_window_and_single_query_rotation_stays_identifiable():
    period = gen.LESSON_SCHEDULE_PERIOD
    assert period == len(gen.SCENE_PROFILES)
    for start in range(period * 2):
        pairs = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED + 1):
            grid = gen.generate(31337, sample_index, difficulty="hard")
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
        for query_index in range(len(pairs)):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert len(demos) == gen.EXAMPLES_NEEDED
            assert gen.lesson_identifiable(demos, pairs[query_index]) == []


def test_default_schedule_anchors_every_canonical_dimension_palette_profile_per_band():
    canonical_profiles = {_palette_profile(pair["input"]) for pair in PAIRS}
    for band in ("easy", "medium", "hard"):
        seen = {
            _palette_profile(gen.generate(9100 + index, index, difficulty=band))
            for index in range(gen.LESSON_SCHEDULE_PERIOD)
        }
        assert canonical_profiles <= seen


def test_validator_rejects_single_seed_inputs_outside_the_teaching_distribution():
    singleton = [[0] * 7 for _ in range(7)]
    singleton[3][3] = 4
    assert any("at least two" in reason for reason in gen.self_check(singleton))


def test_difficulty_bands_are_observably_distinct_without_changing_profile():
    grids = {
        band: gen.generate(4242, 0, difficulty=band)
        for band in ("easy", "medium", "hard")
    }
    assert len({tuple(map(tuple, grid)) for grid in grids.values()}) == 3
    assert {gen.observe_overrides(grid)["scene_profile"] for grid in grids.values()} == {
        gen.schedule_profile(4242, 0)
    }


def test_validator_accepts_footprint_overlap_but_rejects_adjacent_seed_blobs():
    overlap = [[0] * 7 for _ in range(7)]
    overlap[3][2] = 2
    overlap[3][4] = 7
    assert gen.self_check(overlap) == []

    adjacent = deepcopy(overlap)
    adjacent[3][3] = 4
    assert any("isolated" in reason for reason in gen.self_check(adjacent))


@pytest.mark.parametrize("bad", [None, [], [[]], [[0, 0], [0]], [[True, 0], [0, 0]]])
def test_malformed_grids_are_diagnostic_not_exceptions(bad):
    assert gen.self_check(bad)


def test_unknown_overrides_reject_and_replay_is_fresh_and_global_rng_pure():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, typo_axis="bad")
    with pytest.raises(ValueError):
        gen.generate(1, 2, scene_profile="not-a-profile")

    random.seed(991)
    before = random.getstate()
    first = gen.generate(51, 7, difficulty="medium")
    after = random.getstate()
    second = gen.generate(51, 7, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == after


def test_cyclic_lesson_probe_exhausts_all_starts_and_declared_rivals():
    probe_path = TASK_HOME / "workspace" / "cyclic_lesson_probe.py"
    spec = importlib.util.spec_from_file_location("cyclic_lesson_probe", probe_path)
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report = probe.probe_generator(gen, seeds=(17, 23), bands=("easy",))
    assert report["status"] == "no_ambiguity_found"
    assert report["summary"] == {
        "lessons": gen.LESSON_SCHEDULE_PERIOD * 2,
        "rotations": gen.LESSON_SCHEDULE_PERIOD * 2 * (gen.EXAMPLES_NEEDED + 1),
        "ambiguous_rotations": 0,
        "hook_warnings": 0,
        "scoring_errors": 0,
    }
    assert set(report["rivals"]) == set(gen.LESSON_COMPETITORS)
    assert report["schedule_starts"] == list(range(gen.LESSON_SCHEDULE_PERIOD))
