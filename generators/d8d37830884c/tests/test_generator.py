"""Task-local regression tests for the component-size recolouring generator."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import random
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    components,
    gray_only_size_six_output,
    load_generator,
    observed,
    palette_profile,
    rule_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))

EXPECTED_AXES = {
    "grid_h",
    "grid_w",
    "n_size6",
    "n_other",
    "size6_color",
    "other_color",
}


def test_rule_pin_and_honest_axis_surface():
    assert gen.RULE_HASH == "0b5bfbd1622f"
    assert gen.VERSION == "3.0.1"
    assert set(gen.AXES) == EXPECTED_AXES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 3
    assert len(gen.SCHEDULE_PROFILES) == 4


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(),
    ids=lambda pair: f"v{pair['variant']}-{pair['split']}{pair['pair_index']}",
)
def test_accepts_every_canonical_pair_and_independent_oracle_matches(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert rule_output(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {
            "grid_h": 10,
            "grid_w": 10,
            "n_size6": 1,
            "n_other": 1,
            "size6_color": 3,
            "other_color": 3,
        },
        {
            "grid_h": 10,
            "grid_w": 22,
            "n_size6": 3,
            "n_other": 5,
            "size6_color": 9,
            "other_color": 3,
        },
        {
            "grid_h": 22,
            "grid_w": 10,
            "n_size6": 3,
            "n_other": 5,
            "size6_color": 3,
            "other_color": 9,
        },
        {
            "grid_h": 22,
            "grid_w": 22,
            "n_size6": 2,
            "n_other": 4,
            "size6_color": 9,
            "other_color": 9,
        },
    ],
)
def test_joint_exact_overrides_are_constructive_and_pixel_observable(
    difficulty, requested
):
    grid = gen.generate(67_000, 19, difficulty=difficulty, **requested)
    assert gen.self_check(grid) == []
    assert observed(grid) == requested
    assert gen.observe_overrides(grid) == requested
    assert gen.rule_mirror(grid) == rule_output(grid)


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"grid_h": 9},
        {"grid_w": 23},
        {"n_size6": 0},
        {"n_size6": 4},
        {"n_other": 0},
        {"n_other": 6},
        {"size6_color": 0},
        {"size6_color": 2},
        {"other_color": 1},
        {"other_color": 10},
        {"grid_h": True},
        {"grid_w": 10.0},
        {"n_size6": "2"},
        {"n_other": False},
        {"size6_color": 5.0},
    ],
)
def test_invalid_or_unknown_overrides_fail_closed(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, **overrides)


def test_invalid_difficulty_fails_closed():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 2, difficulty="impossible")


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 10 for _ in range(10)],
        [[0] * 9 for _ in range(10)],
        [[0] * 10 for _ in range(9)],
        [[0] * 10 for _ in range(10)],
        [[1] + [0] * 9 for _ in range(10)],
    ],
)
def test_validator_returns_diagnostics_instead_of_raising(grid):
    assert gen.self_check(grid)


def test_canonical_fitting_gray_shortcut_is_real_and_generated_witness_refutes_it():
    assert set(gen.CANONICAL_SHORTCUTS) == {"gray_only_size_six"}
    assert set(gen.LESSON_COMPETITORS) == {"gray_only_size_six"}
    assert all(
        gray_only_size_six_output(pair["input"]) == pair["output"]
        for pair in canonical_pairs()
    )

    witness = gen.generate(901, 2, difficulty="easy")
    assert gen.SEMANTIC_WITNESSES["non_gray_size6"](witness)
    assert gen.rule_mirror(witness) == rule_output(witness)
    assert gen.SEMANTIC_RIVALS["gray_only_size_six"](witness) == gray_only_size_six_output(witness)
    assert rule_output(witness) != gray_only_size_six_output(witness)


def test_four_slot_schedule_balances_canonical_anchors_and_counterexamples():
    for difficulty in (None, "easy", "medium", "hard"):
        for start in range(0, 24, 4):
            grids = [
                gen.generate(700_000 + start, start + offset, difficulty=difficulty)
                for offset in range(4)
            ]
            assert sum(palette_profile(grid) == (10, 10, 2) for grid in grids) == 2
            assert sum(
                gen.SEMANTIC_WITNESSES["non_gray_size6"](grid) for grid in grids
            ) == 2


def test_four_slot_schedule_makes_every_query_rotation_identifiable():
    for difficulty in (None, "easy", "medium", "hard"):
        for start in range(24):
            grids = [
                gen.generate(800_000 + start, start + offset, difficulty=difficulty)
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            profiles = {
                gen.schedule_profile(0, start + offset, difficulty)
                for offset in range(4)
            }
            assert profiles == set(gen.SCHEDULE_PROFILES)
            assert len({json.dumps(grid, separators=(",", ":")) for grid in grids}) == 4
            for query_index in range(4):
                demos = [
                    {"input": deepcopy(grid), "output": rule_output(grid)}
                    for index, grid in enumerate(grids)
                    if index != query_index
                ]
                query = {"input": deepcopy(grids[query_index])}
                assert gen.lesson_identifiable(demos, query) == []
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(
                        rival(demo["input"]) != demo["output"]
                        for demo in demos
                    ), name


def test_each_band_has_canonical_profile_floor_and_broad_semantic_support():
    for difficulty in (None, "easy", "medium", "hard"):
        values = {key: set() for key in EXPECTED_AXES}
        profiles = set()
        other_sizes = set()
        size6_shapes = set()
        witness_hits = 0
        for index in range(240):
            grid = gen.generate(910_000 + index, index, difficulty=difficulty)
            assert gen.self_check(grid) == []
            assert gen.rule_mirror(grid) == rule_output(grid)
            stats = observed(grid)
            for key, value in stats.items():
                values[key].add(value)
            profiles.add(palette_profile(grid))
            found = components(grid)
            other_sizes.update(comp["size"] for comp in found if comp["size"] != 6)
            for comp in found:
                if comp["size"] == 6:
                    r0, c0, r1, c1 = comp["bbox"]
                    normalized = tuple(
                        sorted((r - r0, c - c0) for r, c in comp["cells"])
                    )
                    size6_shapes.add(normalized)
            witness_hits += int(gen.SEMANTIC_WITNESSES["non_gray_size6"](grid))
        assert (10, 10, 2) in profiles
        assert values["n_size6"] == {1, 2, 3}
        assert values["n_other"] == {1, 2, 3, 4, 5}
        assert values["size6_color"] == set(range(3, 10))
        assert values["other_color"] == set(range(3, 10))
        assert {1, 2, 3, 4, 5, 7, 8} <= other_sizes
        assert len(size6_shapes) >= 5
        assert witness_hits == 120


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20261006)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second


def test_generation_is_python_hashseed_independent():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    results = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert results[0] == results[1]


def test_real_racket_authority_matches_independent_oracle():
    from reference_probe import racket_outputs

    grids = [pair["input"] for pair in canonical_pairs()[:4]]
    grids.extend(gen.generate(5100 + index, index) for index in range(12))
    assert racket_outputs(grids) == [rule_output(grid) for grid in grids]
