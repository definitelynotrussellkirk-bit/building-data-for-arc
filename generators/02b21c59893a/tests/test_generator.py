"""Task-local regressions for source-anchor payload transfer semantics."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    CANONICAL_PROFILES,
    RIVALS,
    anchors_payload,
    canonical_pairs,
    clipping_count,
    load_generator,
    observed_profile,
    oracle_output,
    profile_tuple,
    racket_outputs,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_pin_and_public_contract():
    assert gen.VERSION == "4.0.0"
    assert gen.RULE_HASH == "ba8a3944ecbc"
    assert gen.EXAMPLES_NEEDED == 4
    assert gen.MIN_STRICT_FRAC == 1.0
    assert tuple(gen.SCENE_PROFILES) == (
        "canonical_anchor",
        "offset_anchor",
        "last_red",
        "last_red_clip",
        "clip_multicolor",
    )
    assert set(gen.AXES) == {"scene_profile"}
    assert gen.SCHEDULE_PROFILES == gen.SCENE_PROFILES


def test_all_canonical_pairs_are_owned_and_match_independent_oracle():
    pairs = canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(deepcopy(pair["input"])) == []
        assert gen.strict_canonical_like(deepcopy(pair["input"])) == []
        assert oracle_output(deepcopy(pair["input"])) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "profile",
    ["canonical_anchor", "offset_anchor", "last_red", "last_red_clip", "clip_multicolor"],
)
def test_scene_profile_override_is_exact_observable_and_lawful(profile, band):
    for seed in (0, 31, 991):
        grid = gen.generate(seed, 7, difficulty=band, scene_profile=profile)
        assert gen.self_check(grid) == []
        assert observed_profile(grid) == profile
        assert gen.observe_overrides(grid) == {"scene_profile": profile}


@pytest.mark.parametrize(
    "kwargs,exc",
    [
        ({"typo": 1}, TypeError),
        ({"scene_profile": "no_blue"}, ValueError),
        ({"scene_profile": 3}, ValueError),
        ({"difficulty": "legendary"}, ValueError),
    ],
)
def test_invalid_calls_reject_loudly(kwargs, exc):
    with pytest.raises(exc):
        difficulty = kwargs.pop("difficulty", None)
        gen.generate(0, 0, difficulty=difficulty, **kwargs)


def test_every_five_consecutive_indices_visit_every_profile():
    expected = set(gen.SCENE_PROFILES)
    for start in range(40):
        assert {
            gen.schedule_profile(123, start + offset, "medium") for offset in range(5)
        } == expected


def test_profiles_supply_redundant_counterexamples_to_all_declared_rivals():
    expected_witnesses = {
        "canonical_anchor": {"always_origin", "payload_bbox_origin"},
        "offset_anchor": {"always_origin", "payload_bbox_origin"},
        "last_red": {"always_origin", "payload_bbox_origin", "first_red"},
        "last_red_clip": {
            "always_origin",
            "payload_bbox_origin",
            "first_red",
            "all_or_nothing_clip",
        },
        "clip_multicolor": {
            "always_origin",
            "payload_bbox_origin",
            "all_or_nothing_clip",
        },
    }
    for profile, rivals in expected_witnesses.items():
        for index in range(20):
            grid = gen.generate(2_000 + index, index, scene_profile=profile)
            expected = oracle_output(grid)
            for name in rivals:
                assert RIVALS[name](grid) != expected, (profile, name, index)
                assert gen.SEMANTIC_RIVALS[name](deepcopy(grid)) != expected


def test_every_five_pair_query_rotation_is_identifiable():
    for band in ("easy", "medium", "hard"):
        for start in range(30):
            pairs = []
            for offset in range(5):
                grid = gen.generate(9_000 + start, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": oracle_output(grid)})
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert gen.lesson_identifiable(demos, query) == [], (band, start, query_index)


def test_prior_seed_861_all_no_blue_demonstration_defect_is_impossible():
    pairs = []
    for index in range(5):
        grid = gen.generate(861, index, difficulty="medium")
        source, _, _ = anchors_payload(grid)
        assert source != (0, 0)
        assert RIVALS["always_origin"](grid) != oracle_output(grid)
        pairs.append({"input": grid, "output": oracle_output(grid)})
    assert gen.lesson_identifiable(pairs[:4], pairs[4]) == []


def test_canonical_profile_floor_and_palette_reachability_in_every_band():
    for band in ("easy", "medium", "hard"):
        profiles = [
            profile_tuple(gen.generate(50_000 + index, index, difficulty=band))
            for index in range(20)
        ]
        assert sum(profile in CANONICAL_PROFILES for profile in profiles) >= 16
        assert max(palette for _, _, palette in profiles) >= 7


def test_distribution_is_deterministic_and_materially_diverse():
    grids = []
    profiles = set()
    shapes = set()
    for index in range(180):
        band = ("easy", "medium", "hard")[index % 3]
        grid = gen.generate(1_000 + index, index, difficulty=band)
        assert grid == gen.generate(1_000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        grids.append(grid)
        profiles.add(observed_profile(grid))
        shapes.add((len(grid), len(grid[0])))
    assert len({repr(grid) for grid in grids}) >= 170
    assert profiles == set(gen.SCENE_PROFILES)
    assert len(shapes) >= 7


@pytest.mark.parametrize(
    "mutation",
    ["missing_blue", "second_blue", "missing_red", "third_red", "no_payload", "one_payload_colour", "foreign_colour", "ragged", "bool_cell"],
)
def test_self_check_rejects_destructive_mutations(mutation):
    grid = deepcopy(gen.generate(44, 3, scene_profile="last_red_clip"))
    source, reds, payload = anchors_payload(grid)
    if mutation == "missing_blue":
        grid[source[0]][source[1]] = 0
    elif mutation == "second_blue":
        grid[0][0] = 1
    elif mutation == "missing_red":
        for row, col in reds:
            grid[row][col] = 0
    elif mutation == "third_red":
        for row, values in enumerate(grid):
            for col, value in enumerate(values):
                if value == 0:
                    grid[row][col] = 2
                    break
            else:
                continue
            break
    elif mutation == "no_payload":
        for row, col, _ in payload:
            grid[row][col] = 0
    elif mutation == "one_payload_colour":
        for row, col, _ in payload:
            grid[row][col] = 3
    elif mutation == "foreign_colour":
        grid[0][0] = 10
    elif mutation == "ragged":
        grid[-1].pop()
    elif mutation == "bool_cell":
        grid[0][0] = True
    assert gen.self_check(grid), mutation


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True, 0]]])
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_generated_clip_profiles_are_partial_not_total():
    for profile in ("last_red_clip", "clip_multicolor"):
        for index in range(50):
            grid = gen.generate(6_000 + index, index, scene_profile=profile)
            _, _, payload = anchors_payload(grid)
            clipped = clipping_count(grid)
            assert 0 < clipped < len(payload)


def test_generator_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]


def test_real_racket_reference_matches_independent_oracle():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids.extend(gen.generate(500, index, difficulty=("easy", "medium", "hard")[index % 3]) for index in range(30))
    assert racket_outputs(grids) == [oracle_output(grid) for grid in grids]
