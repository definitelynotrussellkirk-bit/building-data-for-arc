"""Focused regressions for the reviewed chamber/legend generator."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "952d011ee8be"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
ROOT = find_root(__file__)


def _pair(grid):
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_rule_pin_and_every_canonical_pair_match_independent_mirror():
    assert GEN.RULE_HASH == "0b4a544c9655"
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {
            "grid_h": 11,
            "grid_w": 10,
            "legend_offset": 0,
            "upper_chambers": 1,
            "split_offset": 0,
            "legend_order": 0,
            "count_order": 0,
        },
        {
            "grid_h": 13,
            "grid_w": 13,
            "legend_offset": 1,
            "upper_chambers": 2,
            "split_offset": 1,
            "legend_order": 3,
            "count_order": 9,
        },
        {
            "grid_h": 15,
            "grid_w": 16,
            "legend_offset": 2,
            "upper_chambers": 3,
            "split_offset": 2,
            "legend_order": 5,
            "count_order": 23,
        },
    ],
)
def test_all_exact_axes_are_constructive_and_observable(band, requested):
    grid = GEN.generate(918273, 17, difficulty=band, **requested)
    assert GEN.self_check(grid, difficulty=band, meta={"overrides": requested}) == []
    assert GEN.observe_overrides(grid) == requested
    assert GEN.rule_mirror(grid) != grid


@pytest.mark.parametrize(
    "bad",
    [
        {"unknown_axis": 1},
        {"grid_h": 10},
        {"grid_h": True},
        {"grid_w": 17},
        {"legend_offset": 3},
        {"upper_chambers": 0},
        {"split_offset": 3},
        {"legend_order": 6},
        {"count_order": 24},
    ],
)
def test_invalid_overrides_fail_closed(bad):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 2, **bad)
    with pytest.raises(ValueError):
        GEN.generate(1, 2, difficulty="extreme")


def test_default_schedule_hits_canonical_profiles_and_varies_every_semantic_axis():
    canonical_shapes = {(11, 10), (11, 11), (11, 12), (12, 11), (12, 12)}
    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(4000 + i, i, difficulty=band) for i in range(48)]
        observed = [GEN.observe_overrides(grid) for grid in grids]
        assert all(GEN.self_check(grid) == [] for grid in grids)
        assert any((item["grid_h"], item["grid_w"]) in canonical_shapes for item in observed)
        assert {item["legend_offset"] for item in observed} == {0, 1, 2}
        assert {item["upper_chambers"] for item in observed} == {1, 2, 3}
        assert {item["split_offset"] for item in observed} == {0, 1, 2}
        assert len({item["legend_order"] for item in observed}) >= 4
        assert len({item["count_order"] for item in observed}) >= 4
        assert len({tuple(map(tuple, grid)) for grid in grids}) >= 44


def test_schedule_profile_accepts_checker_seed_and_sample_index_signature():
    assert GEN.schedule_profile(123456, 17) == GEN.schedule_profile(17)
    assert GEN.schedule_profile(seed=123456, sample_index=17) == GEN.schedule_profile(17)


def test_default_schedule_does_not_lock_independently_overridable_axes_one_to_one():
    profiles = [GEN.schedule_profile(index) for index in range(48)]
    probe_profiles = profiles[:20]

    assert {
        (profile["legend_offset"], profile["split_offset"])
        for profile in probe_profiles
    } == {(legend, split) for legend in range(3) for split in range(3)}

    legend_to_counts = {
        legend_order: {
            profile["count_order"]
            for profile in profiles
            if profile["legend_order"] == legend_order
        }
        for legend_order in {profile["legend_order"] for profile in profiles}
    }
    upper_to_splits = {
        upper_chambers: {
            profile["split_offset"]
            for profile in profiles
            if profile["upper_chambers"] == upper_chambers
        }
        for upper_chambers in {profile["upper_chambers"] for profile in profiles}
    }

    assert all(len(values) >= 3 for values in legend_to_counts.values())
    assert all(values == {0, 1, 2} for values in upper_to_splits.values())


def test_difficulty_bands_are_not_byte_identical_aliases():
    for index in range(12):
        draws = {
            band: GEN.generate(61000 + index, index, difficulty=band)
            for band in ("easy", "medium", "hard")
        }
        assert draws["easy"] != draws["medium"]
        assert draws["easy"] != draws["hard"]
        assert draws["medium"] != draws["hard"]


def test_each_generated_grid_has_two_bands_four_rectangular_chambers_and_all_counts():
    for index in range(36):
        grid = GEN.generate(7000 + index, index, difficulty="hard")
        facts = GEN.analyze(grid)
        assert facts["errors"] == []
        assert len(facts["components"]) == 4
        assert sorted(component["dot_count"] for component in facts["components"]) == [0, 1, 2, 3]
        assert len(facts["full_wall_rows"]) == 3
        assert facts["full_wall_rows"][0] == 2
        assert facts["full_wall_rows"][-1] == len(grid) - 1


def test_canonical_legend_position_shortcut_is_real_and_generated_schedule_refutes_it():
    shortcut = GEN.CANONICAL_SHORTCUTS["legend_at_columns_0_2"]
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs)
    generated = [GEN.generate(8000, index, difficulty="medium") for index in range(8)]
    assert any(GEN.observe_overrides(grid)["legend_offset"] > 0 for grid in generated)
    assert any(shortcut(grid) != GEN.rule_mirror(grid) for grid in generated)


def test_declared_witnesses_are_true_counterexamples_to_named_rivals():
    grids = [GEN.generate(9000 + index, index, difficulty="medium") for index in range(16)]
    assert set(GEN.SEMANTIC_WITNESSES) == set(GEN.WITNESS_RIVALS)
    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        matching = [grid for grid in grids if GEN.SEMANTIC_WITNESSES[witness_name](grid)]
        assert matching, witness_name
        for grid in matching:
            truth = GEN.rule_mirror(grid)
            assert any(GEN.SEMANTIC_RIVALS[name](grid) != truth for name in rival_names)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_four_pair_window_and_query_rotation_refutes_all_declared_competitors(band):
    for start in range(12):
        pairs = [_pair(GEN.generate(12000 + start, start + offset, difficulty=band)) for offset in range(4)]
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                    band,
                    start,
                    query_index,
                    name,
                )


def test_self_check_rejects_targeted_near_misses_and_declared_mutation_fixtures():
    base = GEN.generate(314159, 5, difficulty="medium")
    facts = GEN.analyze(base)

    duplicate_header = deepcopy(base)
    duplicate_header[1] = duplicate_header[0][:]

    broken_wall = deepcopy(base)
    split_row = facts["full_wall_rows"][1]
    broken_wall[split_row][len(base[0]) // 2] = 0

    fourth_legend = deepcopy(base)
    fourth_legend[0][GEN.observe_overrides(base)["legend_offset"] + 3] = 9

    four_dots = deepcopy(base)
    zero_component = next(component for component in facts["components"] if component["dot_count"] == 0)
    for r, c in zero_component["cells"][:4]:
        four_dots[r][c] = 1

    ragged = deepcopy(base)
    ragged[0].pop()

    boolean_cell = deepcopy(base)
    boolean_cell[0][0] = True

    for name, malformed in {
        "duplicate_header": duplicate_header,
        "broken_wall": broken_wall,
        "fourth_legend": fourth_legend,
        "four_dots": four_dots,
        "ragged": ragged,
        "boolean": boolean_cell,
    }.items():
        assert GEN.self_check(malformed), name

    for name, malformed in GEN.mutation_fixtures():
        assert GEN.self_check(malformed), name


def test_generation_helpers_and_rivals_are_deterministic_fresh_and_pure():
    random.seed(24681357)
    state = random.getstate()
    first = GEN.generate(12345, 17, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(12345, 17, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))

    frozen = deepcopy(first)
    assert GEN.rule_mirror(first) == GEN.rule_mirror(second)
    for rival in GEN.SEMANTIC_RIVALS.values():
        rival(first)
        assert first == frozen
    for witness in GEN.SEMANTIC_WITNESSES.values():
        witness(first)
        assert first == frozen
