"""Task-local regression tests for the frame-assignment generator repair."""
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
    canonical_pairs,
    canonical_rule_hash,
    frame_first_output,
    load_generator,
    object_count,
    palette_profile,
    reference_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("index,pair", list(enumerate(canonical_pairs())))
def test_accepts_every_canonical_input_and_matches_independent_oracle(index, pair):
    assert gen.self_check(pair["input"]) == [], f"canonical pair {index} rejected"
    assert reference_output(pair["input"]) == pair["output"]


def test_rule_hash_is_pinned_to_selected_authority():
    assert gen.RULE_HASH == canonical_rule_hash()


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("size", [12, 15, 18])
def test_exact_dimension_overrides_are_honored_in_every_band(band, size):
    grid = gen.generate(17, 9, difficulty=band, grid_h=size, grid_w=size)
    assert (len(grid), len(grid[0])) == (size, size)
    assert gen.observe_overrides(grid) == {"grid_h": size, "grid_w": size}
    assert gen.self_check(grid) == []


@pytest.mark.parametrize("overrides", [
    {"grid_h": 11}, {"grid_h": 19}, {"grid_w": 11}, {"grid_w": 19},
    {"grid_h": True}, {"grid_w": 12.5}, {"typo_axis": 12},
])
def test_invalid_or_unknown_overrides_are_rejected(overrides):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **overrides)


def test_default_distribution_includes_canonical_four_object_scenes():
    counts = {object_count(gen.generate(400 + index, index)) for index in range(90)}
    assert 4 in counts
    assert counts <= {4, 5, 6}


def test_default_schedule_rotates_three_semantic_profiles():
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "centered_slack", "order_competition", "rotation_distractor",
    )
    for start in range(12):
        assert {
            gen.schedule_profile(123, start + offset, difficulty="hard")
            for offset in range(3)
        } == set(gen.SCHEDULE_PROFILES)


@pytest.mark.parametrize("start", range(9))
def test_every_three_example_window_refutes_all_declared_competitors(start):
    demos = []
    for offset in range(3):
        grid = gen.generate(712, start + offset, difficulty="medium")
        demos.append({"input": grid, "output": reference_output(grid)})
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert any(rival(deepcopy(demo["input"])) != demo["output"] for demo in demos), name


def test_generated_profiles_are_real_counterexamples_to_intended_shortcuts():
    grids = {
        gen.schedule_profile(31, index): gen.generate(31, index, grid_h=12, grid_w=12)
        for index in range(3)
    }
    intended = {name: reference_output(grid) for name, grid in grids.items()}
    assert gen.SEMANTIC_RIVALS["top_left_in_frame"](deepcopy(grids["centered_slack"])) != intended["centered_slack"]
    assert gen.SEMANTIC_RIVALS["exact_bbox_only"](deepcopy(grids["centered_slack"])) != intended["centered_slack"]
    assert gen.SEMANTIC_RIVALS["solid_area_order"](deepcopy(grids["order_competition"])) != intended["order_competition"]
    assert gen.SEMANTIC_RIVALS["frame_first"](deepcopy(grids["order_competition"])) != intended["order_competition"]
    assert gen.SEMANTIC_RIVALS["never_rotate"](deepcopy(grids["rotation_distractor"])) != intended["rotation_distractor"]


@pytest.mark.parametrize("name", ["top_left_in_frame", "exact_bbox_only", "solid_area_order"])
def test_declared_canonical_shortcuts_reproduce_all_public_pairs(name):
    shortcut = gen.CANONICAL_SHORTCUTS[name]
    assert all(shortcut(deepcopy(pair["input"])) == pair["output"] for pair in canonical_pairs())


def test_frame_first_is_plausible_but_already_refuted_by_canonical():
    pairs = canonical_pairs()
    assert any(frame_first_output(pair["input"]) != pair["output"] for pair in pairs)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_distribution_is_deterministic_diverse_and_semantically_live(band):
    unique = set()
    profiles = set()
    witness_hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    for index in range(90):
        grid = gen.generate(2100 + index, index * 11, difficulty=band)
        assert grid == gen.generate(2100 + index, index * 11, difficulty=band)
        assert gen.self_check(grid) == []
        unique.add(tuple(tuple(row) for row in grid))
        profiles.add(palette_profile(grid))
        for name, predicate in gen.SEMANTIC_WITNESSES.items():
            witness_hits[name] += bool(predicate(deepcopy(grid)))
    assert len(unique) >= 80
    assert any(profile in {(12, 12, 5), (13, 13, 7), (14, 14, 5), (15, 15, 7)} for profile in profiles)
    assert all(count >= 20 for count in witness_hits.values()), witness_hits


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 12 for _ in range(12)]])
def test_malformed_grids_return_diagnostics_not_exceptions(grid):
    assert gen.self_check(grid)


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    results = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(subprocess.check_output(
            [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
            env=env, text=True,
        ))
    assert results[0] == results[1]


def test_real_racket_reference_when_available():
    from arc_repl.racket_bridge import racket_runtime_status
    from reference_probe import racket_outputs
    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(319, index, difficulty="hard") for index in range(18)]
    assert racket_outputs(grids) == [reference_output(grid) for grid in grids]
