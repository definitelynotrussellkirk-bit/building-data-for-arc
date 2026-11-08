"""Source-bound regression tests for the rotation-match generator."""
from __future__ import annotations

from copy import deepcopy
import itertools
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
    canonical,
    canonical_pairs,
    first_candidate_output,
    load_generator,
    normalized_rule_hash,
    observed,
    racket_outputs,
    rule_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_pin_canonical_pairs_and_first_candidate_shortcut():
    expected_hash = normalized_rule_hash(canonical()["program_solution"])
    assert gen.RULE_HASH == expected_hash
    pairs = canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert pair["input"] == original
        assert rule_output(pair["input"]) == pair["output"]
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        # This is the canonical-fitting shortcut the repaired sampler must teach against.
        assert first_candidate_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_exact_override_cartesian_is_observable_and_lawful_in_every_band(difficulty):
    cases = itertools.product(
        (10, 16),
        (11, 16),
        (4, 7),
        (0, 3),
        ("first", "later"),
        (1, 2),
    )
    for index, (h, w, size, rotation, order, distractors) in enumerate(cases):
        requested = {
            "grid_h": h,
            "grid_w": w,
            "shape_size": size,
            "match_rotation": rotation,
            "match_order": order,
            "n_distractors": distractors,
        }
        grid = gen.generate(91000 + index, index, difficulty=difficulty, **requested)
        assert gen.self_check(grid) == [], requested
        assert observed(grid) == requested
        assert gen.observe_overrides(grid) == requested
        assert gen.rule_mirror(grid) == rule_output(grid)


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"grid_h": 9},
        {"grid_h": 17},
        {"grid_w": 10},
        {"grid_w": 17},
        {"shape_size": 3},
        {"shape_size": 8},
        {"match_rotation": -1},
        {"match_rotation": 4},
        {"match_order": "middle"},
        {"n_distractors": 0},
        {"n_distractors": 3},
        {"grid_h": True},
        {"shape_size": 4.0},
        {"match_rotation": "1"},
        {"match_order": 1},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, **overrides)


def test_invalid_difficulty_is_rejected_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 2, difficulty="impossible")


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_default_schedule_covers_canonical_profiles_and_refutes_shortcut(difficulty):
    assert gen.EXAMPLES_NEEDED == 3
    assert set(gen.CANONICAL_SHORTCUTS) == {"first_candidate"}
    assert set(gen.LESSON_COMPETITORS) == set(gen.CANONICAL_SHORTCUTS)
    assert set(gen.SEMANTIC_RIVALS) == set(gen.CANONICAL_SHORTCUTS)

    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]), len({v for row in pair["input"] for v in row}))
        for pair in canonical_pairs()
    }
    generated_profiles = set()
    for index in range(30):
        grid = gen.generate(7000 + index, index, difficulty=difficulty)
        generated_profiles.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
        assert gen.self_check(grid) == []
        assert gen.rule_mirror(grid) == rule_output(grid)
    assert canonical_profiles <= generated_profiles

    for start in range(30):
        grids = [
            gen.generate(17000 + start, start + offset, difficulty=difficulty)
            for offset in range(4)
        ]
        stats = [observed(grid) for grid in grids]
        assert any(item["match_order"] == "later" for item in stats[:3])
        demos = [{"input": grid, "output": rule_output(grid)} for grid in grids[:3]]
        query = {"input": grids[3], "output": rule_output(grids[3])}
        assert gen.lesson_identifiable(demos, query) == []


def test_declared_shortcut_fits_canonical_but_generated_witnesses_disagree():
    assert all(first_candidate_output(pair["input"]) == pair["output"] for pair in canonical_pairs())
    witnesses = [
        gen.generate(12000 + index, index, match_order="later")
        for index in range(24)
    ]
    assert all(gen.SEMANTIC_WITNESSES["match_not_first"](grid) for grid in witnesses)
    assert all(
        gen.SEMANTIC_RIVALS["first_candidate"](grid) == first_candidate_output(grid)
        for grid in witnesses
    )
    assert all(
        gen.SEMANTIC_RIVALS["first_candidate"](grid) != rule_output(grid)
        for grid in witnesses
    )


def test_validator_rejects_structural_corruption_without_mutating_input():
    grid = gen.generate(
        440,
        8,
        grid_h=12,
        grid_w=13,
        shape_size=7,
        match_rotation=3,
        match_order="later",
        n_distractors=2,
    )
    original = deepcopy(grid)
    assert gen.self_check(grid) == []
    assert grid == original

    mutations = {}
    mutations["blank"] = [[0 for _ in row] for row in grid]
    mutations["ragged"] = deepcopy(grid)
    mutations["ragged"][-1].pop()
    mutations["bad_color"] = deepcopy(grid)
    mutations["bad_color"][0][0] = 10
    mutations["erase_target"] = deepcopy(grid)
    mutations["erase_target"][0][-1] = 0
    mutations["duplicate_reference"] = deepcopy(grid)
    mutations["duplicate_reference"][0][0] = 1

    for name, changed in mutations.items():
        assert gen.self_check(changed), name


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 11 for _ in range(10)]],
)
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_replay_is_deterministic_and_global_rng_pure():
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


def test_default_path_records_every_exact_axis_through_genctx():
    from puzzle_generators.base import set_ctx_observer

    captured = []
    set_ctx_observer(captured.append)
    try:
        grid = gen.generate(77, 4, difficulty="hard")
    finally:
        set_ctx_observer(None)
    assert captured
    draws = captured[-1].recorded_draws()
    assert set(gen.AXES) <= set(draws)
    assert {name: draws[name] for name in gen.AXES} == gen.observe_overrides(grid)


def test_distribution_exercises_all_semantic_axes():
    for difficulty in (None, "easy", "medium", "hard"):
        stats = [observed(gen.generate(22000 + i, i * 11, difficulty=difficulty)) for i in range(192)]
        assert {row["shape_size"] for row in stats} == set(range(4, 8))
        assert {row["match_rotation"] for row in stats} == set(range(4))
        assert {row["match_order"] for row in stats} == {"first", "later"}
        assert {row["n_distractors"] for row in stats} == {1, 2}
        assert len({(row["grid_h"], row["grid_w"]) for row in stats}) >= 12


def test_real_racket_reference_matches_independent_oracle():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [
        gen.generate(319 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
        for index in range(48)
    ]
    assert racket_outputs(grids) == [rule_output(grid) for grid in grids]



def test_reference_probe_cli_is_portable_with_live_racket(tmp_path):
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    repo = HOME.parents[1]
    output = tmp_path / "probe.json"
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join((str(repo / "src"), str(repo / "shared/runtime")))
    completed = subprocess.run(
        [
            sys.executable,
            str(HOME / "workspace" / "reference_probe.py"),
            "--count",
            "1",
            "--racket",
            "--out",
            str(output),
        ],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads(output.read_text())
    assert report["racket"]["status"] == "passed"
    assert report["racket"]["checked"] > 0

def test_difficulty_bands_change_default_instances_without_restricting_overrides():
    triples = [
        tuple(
            json.dumps(gen.generate(33000 + index, index, difficulty=band))
            for band in ("easy", "medium", "hard")
        )
        for index in range(24)
    ]
    assert all(len(set(triple)) == 3 for triple in triples)
