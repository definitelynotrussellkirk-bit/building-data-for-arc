"""Regression and semantic-contract tests for the reviewed two-key maze."""
from __future__ import annotations

from copy import deepcopy
import json
import importlib.util
import os
from pathlib import Path
import sys

import pytest
from reviewer_support import canonical_pairs, find_root

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from two_key_probe import (  # noqa: E402
    always_collect_both_rival,
    classify,
    doors_are_walls_rival,
    erase_keys_and_doors_rival,
    one_key_opens_both_rival,
    rule_output,
)


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("generator_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
CANONICAL = canonical_pairs(gen.TASK_ID, root=find_root(__file__))


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _pair(grid):
    return {"input": deepcopy(grid), "output": rule_output(grid)}


def test_rule_pin_and_honest_public_contract():
    assert gen.RULE_HASH == "e59742fe2660"
    assert gen.EXAMPLES_NEEDED == 5
    assert gen.MIN_STRICT_FRAC >= 0.50
    assert set(gen.AXES) == {"grid_h", "grid_w", "route_profile"}
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "two_stage_detour",
        "unreachable",
        "bypass",
    )
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.HELPFUL_TEXTURES == ()
    assert gen.DEGENERATE_TEXTURES == ()
    assert gen.LAWFUL_DEGENERATE_TEXTURES == ()
    assert isinstance(gen.SOLID_OUTPUT_JUSTIFICATION, str)
    assert len(gen.SOLID_OUTPUT_JUSTIFICATION) >= 30


def test_independent_oracle_and_production_mirror_match_all_canonical_pairs():
    assert len(CANONICAL) == 4
    for pair in CANONICAL:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert classify(pair["input"]) == "two_stage_detour"
        assert rule_output(pair["input"]) == pair["output"]
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_declared_shortcuts_really_fit_every_canonical_pair():
    expected = {
        "erase_keys_and_doors": erase_keys_and_doors_rival,
        "one_key_opens_both": one_key_opens_both_rival,
        "always_collect_both": always_collect_both_rival,
    }
    assert set(gen.CANONICAL_SHORTCUTS) == set(expected)
    for name, rival in expected.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in CANONICAL), name
    assert any(
        doors_are_walls_rival(pair["input"]) != pair["output"]
        for pair in CANONICAL
    )


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("shape", [(7, 12), (9, 14), (13, 18)])
@pytest.mark.parametrize(
    "profile", ["two_stage_detour", "unreachable", "bypass"]
)
def test_exact_overrides_are_constructive_observable_and_correct(
    band, shape, profile
):
    h, w = shape
    grid = gen.generate(
        90210,
        17,
        difficulty=band,
        grid_h=h,
        grid_w=w,
        route_profile=profile,
    )
    assert gen.self_check(grid, difficulty=band) == []
    assert gen.observe_overrides(grid) == {
        "grid_h": h,
        "grid_w": w,
        "route_profile": profile,
    }
    assert classify(grid) == profile
    assert gen.rule_mirror(grid) == rule_output(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_h": 6},
        {"grid_h": 14},
        {"grid_w": 11},
        {"grid_w": 19},
        {"grid_h": True},
        {"grid_w": 14.5},
        {"route_profile": "partial"},
        {"route_profile": 3},
        {"unknown_axis": 1},
        {"difficulty": "impossible"},
    ],
)
def test_invalid_controls_are_rejected(kwargs):
    args = dict(kwargs)
    difficulty = args.pop("difficulty", None)
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty=difficulty, **args)


def test_three_slot_schedule_survives_every_six_pair_query_rotation():
    required = set(gen.SCHEDULE_PROFILES)
    for start in range(18):
        sequence = [gen.schedule_profile(713, start + offset) for offset in range(6)]
        assert set(sequence) == required
        for held_out in range(6):
            assert set(sequence[:held_out] + sequence[held_out + 1 :]) == required


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_rotated_generated_lesson_is_identifiable(band):
    for start in range(6):
        pairs = [
            _pair(gen.generate(1207 + start, start + offset, difficulty=band))
            for offset in range(6)
        ]
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == []
            assert {classify(pair["input"]) for pair in demos} == set(
                gen.SCHEDULE_PROFILES
            )
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(
                    rival(pair["input"]) != pair["output"] for pair in demos
                ), (band, start, query_index, name)


def test_profiles_refute_the_named_shortcuts_and_fire_declared_witnesses():
    assert set(gen.SEMANTIC_WITNESSES) == set(gen.WITNESS_RIVALS)
    assert set(gen.SEMANTIC_RIVALS) == {
        "erase_keys_and_doors",
        "doors_are_walls",
        "one_key_opens_both",
        "always_collect_both",
    }

    grids = {
        profile: gen.generate(
            481516,
            index,
            difficulty="medium",
            grid_h=9,
            grid_w=14,
            route_profile=profile,
        )
        for index, profile in enumerate(gen.SCHEDULE_PROFILES)
    }

    detour = grids["two_stage_detour"]
    truth = rule_output(detour)
    assert truth != erase_keys_and_doors_rival(detour)
    assert truth != doors_are_walls_rival(detour)
    assert truth != one_key_opens_both_rival(detour)

    unreachable = grids["unreachable"]
    assert rule_output(unreachable) != erase_keys_and_doors_rival(unreachable)
    assert rule_output(unreachable) != one_key_opens_both_rival(unreachable)

    bypass = grids["bypass"]
    assert rule_output(bypass) != always_collect_both_rival(bypass)

    fired = {
        name
        for name, witness in gen.SEMANTIC_WITNESSES.items()
        if any(witness(grid) for grid in grids.values())
    }
    assert fired == set(gen.SEMANTIC_WITNESSES)
    for witness, rival_names in gen.WITNESS_RIVALS.items():
        assert rival_names
        for grid in grids.values():
            if gen.SEMANTIC_WITNESSES[witness](grid):
                assert all(
                    gen.SEMANTIC_RIVALS[name](grid) != gen.rule_mirror(grid)
                    for name in rival_names
                )


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_stays_on_manifold_and_varies_topology(band):
    grids = [gen.generate(314159, index, difficulty=band) for index in range(30)]
    assert all(gen.self_check(grid, difficulty=band) == [] for grid in grids)
    assert {classify(grid) for grid in grids} == set(gen.SCHEDULE_PROFILES)
    assert len({_frozen(grid) for grid in grids}) >= 27
    # Four out of every five scheduled shapes are exact canonical dimensions.
    assert sum(bool(gen.strict_canonical_like(grid)) for grid in grids) <= 6


@pytest.mark.parametrize(
    "profile", ["two_stage_detour", "unreachable", "bypass"]
)
def test_seed_changes_exact_shape_topology_not_only_mirror_orientation(profile):
    grids = {
        _frozen(
            gen.generate(
                seed,
                0,
                difficulty="hard",
                grid_h=9,
                grid_w=14,
                route_profile=profile,
            )
        )
        for seed in range(16)
    }
    assert len(grids) >= 12


def test_generation_helpers_and_rivals_are_deterministic_fresh_and_pure():
    for band in (None, "easy", "medium", "hard"):
        for index in range(9):
            first = gen.generate(77, index, difficulty=band)
            second = gen.generate(77, index, difficulty=band)
            assert first == second
            assert first is not second
            assert all(a is not b for a, b in zip(first, second))
            before = deepcopy(first)
            assert gen.rule_mirror(first) == rule_output(first)
            assert gen.observe_overrides(first)["route_profile"] == classify(first)
            for rival in gen.SEMANTIC_RIVALS.values():
                rival(first)
                assert first == before
            for witness in gen.SEMANTIC_WITNESSES.values():
                witness(first)
                assert first == before


def test_self_check_rejects_structural_and_semantic_near_misses():
    good = gen.generate(
        2026,
        4,
        grid_h=9,
        grid_w=14,
        route_profile="two_stage_detour",
    )
    assert gen.self_check(good) == []

    illegal = deepcopy(good)
    illegal[1][1] = 10
    assert gen.self_check(illegal)

    duplicate_key = deepcopy(good)
    zero = next(
        (r, c)
        for r, row in enumerate(duplicate_key)
        for c, value in enumerate(row)
        if value == 0
    )
    duplicate_key[zero[0]][zero[1]] = 4
    assert gen.self_check(duplicate_key)

    broken_border = deepcopy(good)
    broken_border[0][1] = 0
    assert gen.self_check(broken_border)

    ragged = [row[:] for row in good]
    ragged[-1] = ragged[-1][:-1]
    assert gen.self_check(ragged)


@pytest.mark.parametrize(
    "bad",
    [None, [], [[]], [[0], [0, 1]], [[True, 0], [0, 0]], [[10, 0], [0, 0]]],
)
def test_malformed_grids_return_diagnostics_instead_of_raising(bad):
    assert gen.self_check(bad)


def test_retained_erase_keys_and_doors_counterexample_replays():
    fixture_path = HOME / "counterexamples" / "erase_keys_and_doors.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    grid = fixture["input"]
    assert fixture["generator_sha256"] == (
        "25c0279e274f54e6f706b65c4aae39a77fcbe2693831d5ec5c2314926d7a6aee"
    )
    assert gen.self_check(grid, difficulty="medium") == []
    assert gen.rule_mirror(grid) == fixture["authority_output"]
    assert gen.SEMANTIC_RIVALS["erase_keys_and_doors"](grid) == fixture["rival_output"]
    assert fixture["authority_output"] != fixture["rival_output"]
