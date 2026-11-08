"""Regression tests for the strict segment-interior generator."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import os
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "b8cd4b7fd7a4"
HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    analyze,
    axis_only_rival,
    color_three_only_rival,
    endpoint_color_rival,
    include_endpoints_rival,
    intended_output,
    racket_outputs,
)

GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def test_rule_pin_and_exact_axis_contract():
    assert GEN.RULE_HASH == "1b1807245196"
    assert GEN.VERSION == "3.1.0"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.LESSON_SCHEDULE_PERIOD == 8
    assert GEN.MIN_STRICT_FRAC == 1.0
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(GEN.AXES) == {
        "grid_h",
        "grid_w",
        "orientation",
        "endpoint_color",
    }


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "height,width,orientation",
    [
        (5, 14, "horizontal"),
        (14, 5, "vertical"),
        (5, 5, "diagonal"),
        (14, 14, "diagonal"),
    ],
)
@pytest.mark.parametrize("endpoint_color", [1, 3, 7])
def test_every_exact_override_is_constructive_and_observable(
    band, height, width, orientation, endpoint_color
):
    grid = GEN.generate(
        91,
        7,
        difficulty=band,
        grid_h=height,
        grid_w=width,
        orientation=orientation,
        endpoint_color=endpoint_color,
    )
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) == []
    assert GEN.observe_overrides(grid) == {
        "grid_h": height,
        "grid_w": width,
        "orientation": orientation,
        "endpoint_color": endpoint_color,
    }
    assert intended_output(grid) != grid


@pytest.mark.parametrize(
    "key,value",
    [
        ("grid_h", 4),
        ("grid_h", 15),
        ("grid_w", 4),
        ("grid_w", 15),
        ("orientation", "slope"),
        ("endpoint_color", 0),
        ("endpoint_color", 8),
        ("texture", "non_aligned"),
        ("typo_axis", 1),
        ("grid_h", True),
        ("grid_w", 8.5),
        ("endpoint_color", "3"),
        ("orientation", 1),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **{key: value})


@pytest.mark.parametrize(
    "seed,sample_index",
    [
        (True, 0),
        (1.0, 0),
        ("1", 0),
        (0, True),
        (0, 1.0),
        (0, "1"),
        (0, -1),
    ],
)
def test_invalid_request_scalars_are_rejected(seed, sample_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, sample_index)


def test_ordinary_stream_uses_full_color_domain_and_broad_shape_support():
    colors = {
        GEN.observe_overrides(GEN.generate(seed, profile))["endpoint_color"]
        for seed in range(64)
        for profile in GEN.SCHEDULE_PROFILES
    }
    assert colors == set(range(1, 8))

    for band in ("easy", "medium", "hard"):
        broad = [
            GEN.observe_overrides(GEN.generate(seed, 7, difficulty=band))
            for seed in range(256)
        ]
        assert {row["grid_h"] for row in broad} == set(range(5, 15))
        assert {row["grid_w"] for row in broad} == set(range(5, 15))
        assert len({(row["grid_h"], row["grid_w"]) for row in broad}) >= 80


def test_canonical_inputs_are_owned_and_independent_oracle_matches_answers():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert intended_output(pair["input"]) == pair["output"]


def test_color_three_only_is_a_real_canonical_fitting_shortcut():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert set(GEN.CANONICAL_SHORTCUTS) == {"color_three_only"}
    assert all(
        color_three_only_rival(pair["input"]) == pair["output"]
        for pair in pairs
    )


def test_default_schedule_refutes_all_declared_rivals_in_every_rotation():
    expected_rivals = {
        "color_three_only",
        "axis_only",
        "include_endpoints",
        "paint_endpoint_color",
    }
    assert set(GEN.SEMANTIC_RIVALS) == expected_rivals
    assert set(GEN.LESSON_COMPETITORS) == expected_rivals
    for band in ("easy", "medium", "hard"):
        for start in range(16):
            pairs = []
            for index in range(start, start + 4):
                grid = GEN.generate(700 + start, index, difficulty=band)
                pairs.append({"input": grid, "output": intended_output(grid)})
            for query_index, query in enumerate(pairs):
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                assert GEN.lesson_identifiable(demos, query) == [], (
                    band,
                    start,
                    query_index,
                )
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(
                        rival(deepcopy(pair["input"])) != pair["output"]
                        for pair in demos
                    ), (band, start, query_index, name)


def test_declared_witnesses_are_executable_counterexamples():
    grids = [GEN.generate(811, index, difficulty="medium") for index in range(8)]
    truth = [intended_output(grid) for grid in grids]
    fired = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    for grid, expected in zip(grids, truth):
        for name, predicate in GEN.SEMANTIC_WITNESSES.items():
            if predicate(deepcopy(grid)):
                fired[name] += 1
                rivals = GEN.WITNESS_RIVALS.get(name, [])
                if rivals:
                    assert any(
                        GEN.SEMANTIC_RIVALS[rival](deepcopy(grid)) != expected
                        for rival in rivals
                    ), name
    assert all(fired.values()), fired


def test_generation_and_semantic_helpers_do_not_mutate_inputs():
    grid = GEN.generate(101, 203, difficulty="hard")
    original = deepcopy(grid)
    assert intended_output(grid) != grid
    for function in GEN.SEMANTIC_RIVALS.values():
        function(grid)
        assert grid == original
    for predicate in GEN.SEMANTIC_WITNESSES.values():
        predicate(grid)
        assert grid == original
    GEN.strict_canonical_like(grid)
    GEN.observe_overrides(grid)
    assert grid == original


def test_self_check_rejects_semantically_malformed_near_misses():
    cases = {
        "blank": [[0] * 8 for _ in range(8)],
        "one_endpoint": [[3, 0, 0], [0, 0, 0], [0, 0, 0]],
        "adjacent": [[3, 3, 0], [0, 0, 0], [0, 0, 0]],
        "non_aligned": [[3, 0, 0], [0, 0, 3], [0, 0, 0]],
        "mixed_colors": [[3, 0, 4], [0, 0, 0], [0, 0, 0]],
        "three_points": [[3, 0, 3], [0, 0, 0], [3, 0, 0]],
        "bad_color": [[10, 0, 10], [0, 0, 0], [0, 0, 0]],
        "bool_cell": [[True, 0, True], [0, 0, 0], [0, 0, 0]],
        "ragged": [[3, 0, 3], [0, 0]],
    }
    for name, grid in cases.items():
        assert GEN.self_check(grid), name
        with pytest.raises(ValueError):
            GEN.observe_overrides(grid)


def test_schedule_covers_orientations_colors_and_profile_floor():
    canonical_profiles = {(8, 8, 2), (9, 9, 2)}
    pooled_exact = 0
    pooled_envelope = 0
    for band in ("easy", "medium", "hard"):
        orientations = set()
        colors = set()
        exact = 0
        envelope = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            sample_index = seed % 7919 + index
            grid = GEN.generate(seed, sample_index, difficulty=band)
            assert grid == GEN.generate(seed, sample_index, difficulty=band)
            assert GEN.self_check(grid) == []
            info = analyze(grid)
            profile = (
                info["grid_h"],
                info["grid_w"],
                len({value for row in grid for value in row}),
            )
            orientations.add(info["orientation"])
            colors.add(info["endpoint_color"])
            exact += profile in canonical_profiles
            envelope += (
                8 <= profile[0] <= 9
                and 8 <= profile[1] <= 9
                and profile[2] == 2
            )
        assert orientations == {"horizontal", "vertical", "diagonal"}, band
        assert 3 in colors and len(colors) >= 4, (band, colors)
        assert exact >= 1, band
        assert envelope >= 5, band
        pooled_exact += exact
        pooled_envelope += envelope
    assert pooled_exact >= 3
    assert pooled_envelope >= 15


def test_independent_rivals_match_declared_implementations():
    mapping = {
        "color_three_only": color_three_only_rival,
        "axis_only": axis_only_rival,
        "include_endpoints": include_endpoints_rival,
        "paint_endpoint_color": endpoint_color_rival,
    }
    for index in range(12):
        grid = GEN.generate(912, index)
        for name, rival in mapping.items():
            assert GEN.SEMANTIC_RIVALS[name](deepcopy(grid)) == rival(grid)


def test_real_racket_reference_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [
        pair["input"]
        for pair in canonical_pairs(TASK_ID, root=find_root(__file__))
    ]
    grids += [GEN.generate(319, index, difficulty=("easy", "medium", "hard")[index % 3]) for index in range(12)]
    assert racket_outputs(grids) == [intended_output(grid) for grid in grids]
