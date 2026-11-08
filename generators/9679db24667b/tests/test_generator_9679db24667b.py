"""Regression, contract, and lesson-identifiability tests for 9679db24667b."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import itertools
import os
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "9679db24667b"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    source = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("generator_9679db24667b_under_test", source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _pair(grid):
    return {"input": deepcopy(grid), "output": GEN.rule_mirror(grid)}


def _row_facts(grid):
    facts = []
    for row in grid:
        colors = {value for value in row if value not in (0, 9)}
        facts.append(
            {
                "nines": row.count(9),
                "colors": colors,
                "colored_cells": sum(value not in (0, 9) for value in row),
            }
        )
    return facts


def test_rule_pin_and_all_canonical_pairs_match_without_mutation():
    assert GEN.RULE_HASH == "7ebc4d35864a"
    pairs = _pairs()
    assert len(pairs) == 4
    for pair in pairs:
        source = deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_unknown_invalid_and_out_of_range_overrides_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=7)
    for name in GEN.AXES:
        for invalid in (True, 7.0, "7"):
            with pytest.raises((TypeError, ValueError), match=name):
                GEN.generate(1, 0, **{name: invalid})
    with pytest.raises((TypeError, ValueError), match="grid_h"):
        GEN.generate(1, 0, grid_h=5)
    with pytest.raises((TypeError, ValueError), match="grid_w"):
        GEN.generate(1, 0, grid_w=13)
    with pytest.raises((TypeError, ValueError), match="n_positive_rows"):
        GEN.generate(1, 0, n_positive_rows=4)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_override_boundary_cross_product_is_exact_and_constructive(band):
    for h, w, n_positive in itertools.product((6, 10), (8, 12), (1, 3)):
        overrides = {
            "grid_h": h,
            "grid_w": w,
            "n_positive_rows": n_positive,
        }
        for sample_index in (0, 1):  # canonical and teaching schedules
            grid = GEN.generate(1901, sample_index, difficulty=band, **overrides)
            assert GEN.self_check(grid, difficulty=band, meta=overrides) == []
            assert GEN.observe_overrides(grid) == overrides
            assert GEN.rule_mirror(grid) != grid


def test_schedule_alternates_and_every_rotated_four_pair_lesson_keeps_a_teacher():
    assert tuple(GEN.SCHEDULE_PROFILES) == ("canonical", "teaching")
    assert GEN.EXAMPLES_NEEDED == 3
    for band in (None, "easy", "medium", "hard"):
        for start in range(12):
            profiles = [
                GEN.schedule_profile(701, index, band)
                for index in range(start, start + 4)
            ]
            assert profiles == [
                ("canonical", "teaching")[(start + offset) % 2]
                for offset in range(4)
            ]
            for held_out in range(4):
                demos = [profile for i, profile in enumerate(profiles) if i != held_out]
                assert "teaching" in demos


def test_teaching_profile_realizes_each_decisive_witness():
    grid = GEN.generate(
        8801,
        1,
        difficulty="hard",
        grid_h=6,
        grid_w=8,
        n_positive_rows=3,
    )
    assert GEN.schedule_profile(8801, 1, "hard") == "teaching"
    assert GEN.self_check(grid) == []
    facts = _row_facts(grid)
    positives = [fact for fact in facts if len(fact["colors"]) == 1 and fact["nines"]]
    nine_only = [fact for fact in facts if not fact["colors"] and fact["nines"]]
    multi = [fact for fact in facts if len(fact["colors"]) >= 2 and fact["nines"]]
    assert len(positives) == 3
    assert all(fact["nines"] >= 2 and fact["colored_cells"] >= 2 for fact in positives)
    assert len(nine_only) == 1
    assert len(multi) == 1
    for name, witness in GEN.SEMANTIC_WITNESSES.items():
        assert witness(grid), name


def test_named_canonical_shortcuts_fit_canonical_but_teaching_kills_them():
    pairs = _pairs()
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name

    teaching = GEN.generate(4201, 1, difficulty="medium")
    intended = GEN.rule_mirror(teaching)
    for name, rival in GEN.SEMANTIC_RIVALS.items():
        assert rival(teaching) != intended, name


def test_every_consecutive_lesson_and_each_query_rotation_is_identifiable():
    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        for start in range(10):
            seed = 14_000 + 1_000 * band_index + start
            pairs = [_pair(GEN.generate(seed, index, difficulty=band)) for index in range(start, start + 4)]
            assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []
            for held_out in range(4):
                demos = [pair for i, pair in enumerate(pairs) if i != held_out]
                assert GEN.lesson_identifiable(demos, pairs[held_out]) == []


def test_self_check_rejects_structural_impostors():
    teaching = GEN.generate(3301, 1, grid_h=6, grid_w=8, n_positive_rows=2)
    facts = _row_facts(teaching)

    no_positive = [[0 for _ in row] for row in teaching]
    assert GEN.self_check(no_positive)

    duplicate_positive_color = deepcopy(teaching)
    positive_rows = [
        index
        for index, fact in enumerate(facts)
        if len(fact["colors"]) == 1 and fact["nines"]
    ]
    first_color = next(iter(facts[positive_rows[0]]["colors"]))
    second_color = next(iter(facts[positive_rows[1]]["colors"]))
    duplicate_positive_color[positive_rows[1]] = [
        first_color if value == second_color else value
        for value in duplicate_positive_color[positive_rows[1]]
    ]
    assert GEN.self_check(duplicate_positive_color)

    color_only = deepcopy(teaching)
    positive_row = positive_rows[0]
    color_only[positive_row] = [0 if value == 9 else value for value in color_only[positive_row]]
    assert GEN.self_check(color_only)

    ragged = deepcopy(teaching)
    ragged[-1].pop()
    assert GEN.self_check(ragged)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20261005)
    state = random.getstate()
    first = GEN.generate(1234, 17, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(1234, 17, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 0
    assert first != second


def test_difficulty_bands_are_live_without_changing_exact_axis_contracts():
    samples = {
        band: [GEN.generate(9901, index, difficulty=band) for index in range(12)]
        for band in ("easy", "medium", "hard")
    }
    assert len({repr(samples[band]) for band in samples}) == 3
    for band, grids in samples.items():
        for grid in grids:
            observed = GEN.observe_overrides(grid)
            assert 6 <= observed["grid_h"] <= 10
            assert 8 <= observed["grid_w"] <= 12
            assert 1 <= observed["n_positive_rows"] <= 3


def test_workspace_probe_is_independent_and_matches_canonical_and_generated_cases():
    probe_path = HOME / "workspace" / "reference_probe.py"
    spec = importlib.util.spec_from_file_location("probe_9679db24667b", probe_path)
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    grids = [pair["input"] for pair in _pairs()]
    grids += [GEN.generate(811, index, difficulty="hard") for index in range(8)]
    for grid in grids:
        before = deepcopy(grid)
        assert probe.independent_oracle(grid) == GEN.rule_mirror(grid)
        assert grid == before
        facts = probe.classify_rows(grid)
        assert len(facts) == len(grid)


def test_every_default_canonical_schedule_slot_is_an_exact_public_profile():
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]), len({cell for row in pair["input"] for cell in row}))
        for pair in _pairs()
    }
    assert canonical_profiles == {(6, 8, 4), (7, 9, 4), (8, 10, 5), (9, 10, 5)}
    for band in ("easy", "medium", "hard"):
        for index in range(40):
            if GEN.schedule_profile(17_001, index, band) != "canonical":
                continue
            grid = GEN.generate(17_001, index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({cell for row in grid for cell in row}),
            )
            assert profile in canonical_profiles
