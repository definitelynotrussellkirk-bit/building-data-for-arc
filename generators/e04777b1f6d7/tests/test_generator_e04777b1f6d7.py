"""Focused regression tests for the e04777b1f6d7 semantic generator repair."""
from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.per_puzzle.e04777b1f6d7 import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


TASK_ID = "e04777b1f6d7"


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_pin_and_every_canonical_pair_match_exact_shape_authority():
    assert gen.VERSION == "3.0.0"
    assert gen.RULE_HASH == "672d7e42ddc1"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert gen.rule_mirror(source) == pair["output"]
        assert source == pair["input"]
        # The canonical lesson deliberately contains same-size nonmatches.
        assert gen.SEMANTIC_RIVALS["size_only"](source) != pair["output"]


def test_every_two_demo_schedule_window_identifies_the_rule():
    for difficulty in ("easy", "medium", "hard"):
        grids = [gen.generate(1701, index, difficulty=difficulty) for index in range(8)]
        for start in range(7):
            demos = [_pair(grids[start]), _pair(grids[start + 1])]
            query_grid = gen.generate(1701, start + 20, difficulty=difficulty)
            assert gen.lesson_identifiable(demos, _pair(query_grid)) == []
            profiles = {
                gen.schedule_profile(1701, start, difficulty),
                gen.schedule_profile(1701, start + 1, difficulty),
            }
            assert any(profile.startswith("rotation:") for profile in profiles)
            assert any(profile.startswith("reflection:") for profile in profiles)
            for name, competitor in gen.LESSON_COMPETITORS.items():
                assert any(competitor(pair["input"]) != pair["output"] for pair in demos), name


def test_all_exact_axes_are_observable_across_boundaries():
    cases = [
        {"layout_profile": name} for name in gen.LAYOUT_PROFILES
    ] + [
        {"n_objects": n} for n in range(3, 9)
    ] + [
        {"n_colors": n} for n in (2, 3)
    ] + [
        {"probe_kind": kind} for kind in gen.PROBE_KINDS
    ] + [
        {"match_slot": slot} for slot in gen.MATCH_SLOTS
    ] + [
        {"pair_profile": profile} for profile in gen.PAIR_PROFILES
    ]
    for index, requested in enumerate(cases):
        grid = gen.generate(8000 + index, index, difficulty="medium", **requested)
        assert gen.self_check(grid) == []
        observed = gen.observe_overrides(grid)
        for key, value in requested.items():
            assert observed[key] == value

    full = {
        "layout_profile": "expanded_14x20",
        "n_objects": 8,
        "n_colors": 3,
        "probe_kind": "reflection",
        "match_slot": "spanning",
        "pair_profile": "two_pairs",
    }
    assert gen.observe_overrides(gen.generate(99, 4, difficulty="hard", **full)) == full

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis="x")
    with pytest.raises(ValueError, match="incompatible overrides"):
        gen.generate(1, 0, n_objects=3, pair_profile="two_pairs")
    with pytest.raises(ValueError, match="layout capacity"):
        gen.generate(1, 0, layout_profile="canonical_9x14", n_objects=8)


def test_replay_returns_fresh_objects_and_preserves_global_rng():
    random.seed(20260729)
    before = random.getstate()
    first = gen.generate(123, 7, difficulty="hard")
    assert random.getstate() == before
    second = gen.generate(123, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second


def test_structural_checker_rejects_targeted_impostors():
    lawful = gen.generate(444, 2, difficulty="medium")
    assert gen.self_check(lawful) == []

    malformed = copy.deepcopy(lawful)
    malformed[0] = malformed[0][:-1]

    unexpected_color = copy.deepcopy(lawful)
    unexpected_color[0][0] = 7

    diagonal_touch = [[0] * 9 for _ in range(7)]
    diagonal_touch[1][1] = diagonal_touch[1][2] = 2
    diagonal_touch[2][1] = 2
    diagonal_touch[3][2] = diagonal_touch[3][3] = 3
    diagonal_touch[4][2] = 3

    too_few = [[0] * 9 for _ in range(7)]
    too_few[1][1] = too_few[1][2] = 2

    oversized = [[0] * 14 for _ in range(9)]
    for column in range(9):
        oversized[1][column] = 2
    oversized[5][1] = oversized[5][2] = 3

    fixtures = {
        "malformed": malformed,
        "unexpected_color": unexpected_color,
        "diagonal_touch": diagonal_touch,
        "too_few": too_few,
        "oversized": oversized,
    }
    for name, grid in fixtures.items():
        assert gen.self_check(grid), name


def test_transform_probes_are_same_size_but_not_exact_matches():
    for kind in gen.PROBE_KINDS:
        grid = gen.generate(
            5150,
            1,
            difficulty="hard",
            layout_profile="expanded_12x18",
            n_objects=6,
            n_colors=3,
            probe_kind=kind,
            match_slot="spanning",
            pair_profile="two_pairs",
        )
        analysis = gen._analysis(grid)
        assert analysis is not None
        assert analysis["probe_kind"] == kind
        assert len({len(record["cells"]) for record in analysis["records"]}) == 1
        assert gen.SEMANTIC_RIVALS[f"{kind}_equivalence"](grid) != gen.rule_mirror(grid)
        assert gen.SEMANTIC_RIVALS["dihedral_equivalence"](grid) != gen.rule_mirror(grid)
