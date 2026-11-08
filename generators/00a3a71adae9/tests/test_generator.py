"""Focused contract, semantic, and authority tests for 00a3a71adae9."""
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
    canonical_pairs,
    load_generator,
    observed,
    reference_output,
    rival_outputs,
    semantic_profile,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
PROFILES = ("overlap_priority", "distance_priority", "scan_tiebreak")
BANDS = (None, "easy", "medium", "hard")


@pytest.mark.parametrize("pair", canonical_pairs(), ids=("train0", "train1", "test0"))
def test_canonical_pairs_are_accepted_and_match_independent_oracle(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert reference_output(pair["input"]) == pair["output"]
    assert pair["input"] == original


def test_authority_pin_and_semantic_contract_are_declared():
    assert gen.RULE_HASH == "cdd6424b9ac7"
    assert gen.VERSION != "1.2.1"
    assert tuple(gen.SCHEDULE_PROFILES) == PROFILES
    assert gen.HELPFUL_TEXTURES == gen.SCHEDULE_PROFILES
    assert gen.DEGENERATE_TEXTURES == ()
    assert gen.LAWFUL_DEGENERATE_TEXTURES == ()
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 5
    assert set(gen.SEMANTIC_RIVALS) == {
        "distance_only", "overlap_then_scan", "reverse_scan_tie"
    }
    assert set(gen.LESSON_COMPETITORS) == set(gen.SEMANTIC_RIVALS)


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("texture", PROFILES)
@pytest.mark.parametrize(
    "axes",
    (
        {"grid_h": 10, "grid_w": 12, "n": 2, "motif_size": 1, "mask_cells": 3},
        {"grid_h": 12, "grid_w": 14, "n": 4, "motif_size": 10, "mask_cells": 6},
        {"grid_h": 11, "grid_w": 13, "n": 3, "motif_size": 4, "mask_cells": 5},
    ),
)
def test_every_public_override_is_exact_and_observable_in_every_band(band, texture, axes):
    expected = dict(axes, texture=texture)
    grid = gen.generate(1701, 29, difficulty=band, **expected)
    assert gen.self_check(grid) == []
    assert observed(grid) == expected
    assert gen.observe_overrides(grid) == expected
    assert grid == gen.generate(1701, 29, difficulty=band, **expected)


@pytest.mark.parametrize(
    "overrides",
    (
        {"typo_axis": 1},
        {"grid_h": 9}, {"grid_h": 13}, {"grid_w": 11}, {"grid_w": 15},
        {"n": 1}, {"n": 5}, {"motif_size": 0},
        {"mask_cells": 2}, {"mask_cells": 7}, {"texture": "default"},
        {"grid_h": True}, {"grid_w": 12.0}, {"n": "3"},
        {"motif_size": 11}, {"motif_size": 3.0}, {"mask_cells": False}, {"texture": 1},
    ),
)
def test_invalid_and_unknown_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("difficulty", ("trivial", 0.5, True))
def test_invalid_difficulty_is_rejected(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize(
    "texture,rival",
    (
        ("overlap_priority", "distance_only"),
        ("distance_priority", "overlap_then_scan"),
        ("scan_tiebreak", "reverse_scan_tie"),
    ),
)
def test_each_scheduled_profile_is_a_real_counterexample(texture, rival):
    for n in (2, 3, 4):
        grid = gen.generate(
            711, n, grid_h=10, grid_w=12, n=n,
            motif_size=4, mask_cells=6, texture=texture,
        )
        intended = reference_output(grid)
        assert semantic_profile(grid) == texture
        assert rival_outputs(grid)[rival] != intended
        assert gen.SEMANTIC_RIVALS[rival](grid) == rival_outputs(grid)[rival]
        assert gen.SEMANTIC_WITNESSES[texture](grid)
        assert rival in gen.WITNESS_RIVALS[texture]


@pytest.mark.parametrize("band", BANDS)
def test_default_schedule_covers_all_rule_precedence_levels_and_axes(band):
    profiles, sizes, counts, shapes, grids, outputs = set(), set(), set(), set(), set(), set()
    for index in range(144):
        grid = gen.generate(9000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert grid == gen.generate(9000 + index, index, difficulty=band)
        stats = observed(grid)
        assert stats == gen.observe_overrides(grid)
        assert stats["texture"] == gen.schedule_profile(9000 + index, index, difficulty=band)
        profiles.add(stats["texture"])
        sizes.add(stats["motif_size"])
        counts.add(stats["n"])
        shapes.add((stats["grid_h"], stats["grid_w"]))
        grids.add(json.dumps(grid, separators=(",", ":")))
        outputs.add(json.dumps(reference_output(grid), separators=(",", ":")))
    assert profiles == set(PROFILES)
    assert sizes == set(range(1, 11))
    assert counts == {2, 3, 4}
    assert {(10, 12), (10, 13), (11, 13)} <= shapes
    assert len(grids) >= 130
    assert len(outputs) >= 100


@pytest.mark.parametrize("band", BANDS)
def test_six_example_schedule_survives_every_query_rotation(band):
    # Three profiles repeat twice. Removing any query leaves at least one labeled
    # demonstration of each comparator level, so no declared competitor can fit
    # all demonstrations and change the held-out answer.
    for start in range(18):
        lesson = []
        for offset in range(6):
            index = start * 11 + offset
            grid = gen.generate(31000 + start, index, difficulty=band)
            lesson.append({"input": grid, "output": reference_output(grid)})
        assert {semantic_profile(pair["input"]) for pair in lesson} == set(PROFILES)
        for query_index, query in enumerate(lesson):
            demos = lesson[:query_index] + lesson[query_index + 1 :]
            assert gen.lesson_identifiable(demos, query) == []


def test_canonical_shortcuts_fit_all_canonical_labels_but_have_generated_counterexamples():
    pairs = canonical_pairs()
    for name, solve in gen.CANONICAL_SHORTCUTS.items():
        assert all(solve(pair["input"]) == pair["output"] for pair in pairs), name
        assert any(
            solve(gen.generate(520, i, texture=profile))
            != reference_output(gen.generate(520, i, texture=profile))
            for i, profile in enumerate(PROFILES)
        ), name


@pytest.mark.parametrize(
    "grid",
    (
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 12 for _ in range(10)],
        [[0] * 12 for _ in range(10)],
        [[3] + [0] * 11 for _ in range(10)],
    ),
)
def test_malformed_or_rule_crashing_grids_are_diagnostic_not_exceptions(grid):
    assert gen.self_check(grid)


def test_validator_rejects_destructive_mutations_but_accepts_all_canonical_inputs():
    grid = gen.generate(55, 8, texture="overlap_priority")
    mutations = []
    bad = deepcopy(grid); bad[0][0] = 9; mutations.append(bad)
    bad = deepcopy(grid)
    for r, row in enumerate(bad):
        for c, value in enumerate(row):
            if value == 1: bad[r][c] = 0
    mutations.append(bad)
    bad = deepcopy(grid)
    for r, row in enumerate(bad):
        for c, value in enumerate(row):
            if value == 2: bad[r][c] = 0
    mutations.append(bad)
    assert all(gen.self_check(bad) for bad in mutations)
    assert all(gen.self_check(pair["input"]) == [] for pair in canonical_pairs())


def test_observer_classifies_canonical_precedence_profiles():
    profiles = [gen.observe_overrides(pair["input"])["texture"] for pair in canonical_pairs()]
    assert profiles == ["distance_priority", "distance_priority", "overlap_priority"]


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "g=load_generator(sys.argv[2]);"
        "print(json.dumps(g.generate(31,8,difficulty='hard')))"
    )
    results = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(subprocess.check_output(
            [sys.executable, "-B", "-c", script, str(HOME / "workspace"), str(HOME / "generator.py")],
            env=env, text=True,
        ))
    assert results[0] == results[1]


def test_real_racket_authority_matches_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status
    from reference_probe import racket_outputs
    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(700, i, texture=PROFILES[i % 3]) for i in range(18)]
    original = deepcopy(grids)
    assert racket_outputs(grids) == [reference_output(grid) for grid in grids]
    assert grids == original
