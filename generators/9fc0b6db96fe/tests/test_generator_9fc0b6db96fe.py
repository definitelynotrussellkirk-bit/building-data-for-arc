"""Focused regression tests for transform-the-legend-ordered-gallery."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    LEGEND_POSITIONS,
    PROFILE_SPECS,
    body_scan_order,
    canonical_pairs,
    gallery_output,
    legend_order,
    load_generator,
    observed,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def pair(grid):
    return {"input": grid, "output": gallery_output(grid)}


def test_rule_hash_and_public_axes_are_exact():
    assert gen.RULE_HASH == "0235d1a8fb27"
    assert set(gen.AXES) == {"profile", "key", "legend_layout"}
    assert getattr(gen, "INCOMPATIBLE_OVERRIDE_COMBINATIONS", None) == []


@pytest.mark.parametrize("example", canonical_pairs(), ids=["train0", "train1", "train2", "train3", "test0"])
def test_accepts_canonical_examples_and_independent_oracle_matches(example):
    assert gen.self_check(example["input"]) == []
    assert gallery_output(example["input"]) == example["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", sorted(PROFILE_SPECS))
@pytest.mark.parametrize("layout", ["contiguous", "spaced", "mixed"])
@pytest.mark.parametrize("key", [1, 2, 3, 4])
def test_every_exact_override_is_honored_and_observable(band, profile, layout, key):
    grid = gen.generate(
        1701,
        key * 100 + len(profile) * 10 + len(layout),
        difficulty=band,
        profile=profile,
        key=key,
        legend_layout=layout,
    )
    expected = {"profile": profile, "key": key, "legend_layout": layout}
    assert gen.self_check(grid) == []
    assert observed(grid) == expected
    assert gen.observe_overrides(grid) == expected
    assert legend_order(grid) != body_scan_order(grid)
    assert gallery_output(grid) != gallery_output(grid, legend_order=False)
    if key != 1:
        assert gallery_output(grid) != gallery_output(grid, apply_key=False)


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 1},
        {"profile": "h8_w8_n3"},
        {"profile": 3},
        {"key": 0},
        {"key": 5},
        {"key": True},
        {"key": "2"},
        {"legend_layout": "diagonal"},
        {"legend_layout": 2},
    ],
)
def test_invalid_or_unknown_overrides_fail_loudly(overrides):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_covers_every_semantic_axis_in_each_band(band):
    profiles = set()
    layouts = set()
    keys = set()
    unique = set()
    for index in range(256):
        grid = gen.generate(8100 + index, index * 13 + 5, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert grid == gen.generate(8100 + index, index * 13 + 5, difficulty=band)
        stats = observed(grid)
        profiles.add(stats["profile"])
        layouts.add(stats["legend_layout"])
        keys.add(stats["key"])
        unique.add(json.dumps(grid, separators=(",", ":")))
        assert legend_order(grid) != body_scan_order(grid)
        assert gallery_output(grid) != gallery_output(grid, legend_order=False)
        if stats["key"] != 1:
            assert gallery_output(grid) != gallery_output(grid, apply_key=False)
    assert profiles == set(PROFILE_SPECS)
    assert layouts == {"contiguous", "spaced", "mixed"}
    assert keys == {1, 2, 3, 4}
    assert len(unique) >= 240


def test_difficulty_bands_change_the_sampling_schedule():
    differing = 0
    for index in range(64):
        grids = [gen.generate(4400 + index, index * 17 + 1, difficulty=band) for band in ("easy", "medium", "hard")]
        differing += len({json.dumps(grid, separators=(",", ":")) for grid in grids}) > 1
    assert differing >= 40


@pytest.mark.parametrize("mutation", ["bad_key", "dirty_separator", "duplicate_legend", "missing_body", "unknown_body", "scan_order_legend"])
def test_validator_rejects_semantic_mutations(mutation):
    grid = gen.generate(
        19,
        7,
        profile="h9_w15_n4",
        key=2,
        legend_layout="spaced",
    )
    if mutation == "bad_key":
        grid[0][0] = 0
    elif mutation == "dirty_separator":
        grid[1][0] = 6
    elif mutation == "duplicate_legend":
        entries = [(c, v) for c, v in enumerate(grid[0]) if c and v]
        grid[0][entries[1][0]] = entries[0][1]
    elif mutation == "missing_body":
        color = legend_order(grid)[0]
        for row in grid[2:]:
            for c, value in enumerate(row):
                if value == color:
                    row[c] = 0
    elif mutation == "unknown_body":
        grid[1][0] = 9 if 9 not in legend_order(grid) else 8
    elif mutation == "scan_order_legend":
        positions = [c for c, v in enumerate(grid[0]) if c and v]
        for c, color in zip(positions, body_scan_order(grid)):
            grid[0][c] = color
    assert gen.self_check(grid)


@pytest.mark.parametrize("malformed", [None, [], [[]], [[0], [0, 1]], [[True] * 15 for _ in range(9)]])
def test_malformed_grid_is_diagnostic_not_exception(malformed):
    assert gen.self_check(malformed)


def test_semantic_witnesses_refute_named_rivals():
    nonidentity = gen.generate(
        71,
        2,
        profile="h11_w13_n4",
        key=3,
        legend_layout="mixed",
    )
    identity = gen.generate(
        72,
        3,
        profile="h9_w15_n3",
        key=1,
        legend_layout="contiguous",
    )
    truth_nonidentity = gallery_output(nonidentity)
    truth_identity = gallery_output(identity)
    assert gen.reference_output(nonidentity) == truth_nonidentity
    assert gen.reference_output(identity) == truth_identity
    assert gen.SEMANTIC_WITNESSES["legend_order_changes_answer"](nonidentity)
    assert gen.SEMANTIC_RIVALS["body_scan_order"](nonidentity) != truth_nonidentity
    assert gen.SEMANTIC_WITNESSES["key_transform_changes_answer"](nonidentity)
    assert gen.SEMANTIC_RIVALS["ignore_key"](nonidentity) != truth_nonidentity
    assert not gen.SEMANTIC_WITNESSES["key_transform_changes_answer"](identity)
    assert gen.SEMANTIC_RIVALS["ignore_key"](identity) == truth_identity


def test_lesson_hook_detects_surviving_query_changing_rival():
    demos = [
        pair(gen.generate(301, 0, profile="h9_w15_n4", key=1, legend_layout="spaced")),
        pair(gen.generate(302, 1, profile="h9_w14_n4", key=1, legend_layout="mixed")),
        pair(gen.generate(303, 2, profile="h12_w15_n3", key=1, legend_layout="contiguous")),
    ]
    query_grid = gen.generate(304, 3, profile="h11_w13_n4", key=2, legend_layout="spaced")
    reasons = gen.lesson_identifiable(demos, pair(query_grid))
    assert any("ignore_key" in reason for reason in reasons)

    strong_demos = demos[:1] + [
        pair(gen.generate(305, 4, profile="h9_w15_n3", key=3, legend_layout="mixed")),
        pair(gen.generate(306, 5, profile="h11_w13_n4", key=4, legend_layout="contiguous")),
    ]
    assert gen.lesson_identifiable(strong_demos, pair(query_grid)) == []


def test_keyed_rng_is_independent_of_python_hash_seed():
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


def test_real_racket_reference_when_available():
    from arc_repl.racket_bridge import racket_runtime_status
    from reference_probe import racket_outputs

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [example["input"] for example in canonical_pairs()]
    grids.extend(
        gen.generate(
            990 + i,
            i,
            profile=profile,
            key=key,
            legend_layout=layout,
        )
        for i, (profile, key, layout) in enumerate(
            (profile, key, layout)
            for profile in PROFILE_SPECS
            for key in (1, 2, 3, 4)
            for layout in LEGEND_POSITIONS[PROFILE_SPECS[profile][2]]
        )
    )
    assert racket_outputs(grids) == [gallery_output(grid) for grid in grids]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_consecutive_four_default_draws_identify_key_for_all_cyclic_queries(band):
    """The trainer's 3-demo+query windows must always refute ignore-key."""
    for seed in (11, 207020181343618, 73790274206230, 194807966399432):
        for start in range(8):
            pairs = [pair(gen.generate(seed, start + offset, difficulty=band)) for offset in range(4)]
            assert {example["input"][0][0] for example in pairs} == {1, 2, 3, 4}
            for cyclic_start in range(4):
                rotated = pairs[cyclic_start:] + pairs[:cyclic_start]
                assert gen.lesson_identifiable(rotated[:3], rotated[3]) == []
