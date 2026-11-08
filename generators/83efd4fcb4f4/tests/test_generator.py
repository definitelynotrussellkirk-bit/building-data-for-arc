"""Task-local regression suite for 83efd4fcb4f4.

The semantic oracle and rivals live in workspace/plus_probe.py and do not import
production code, so these tests can detect a generator implementation mistake.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
RUNTIME = REPO / "shared" / "runtime"
for path in (RUNTIME, HOME / "workspace"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from plus_probe import (
    RIVALS,
    WITNESSES,
    distractor_components,
    rule_output,
    true_centers,
)
from reviewer_support import canonical_pairs


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("generator_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _canonical():
    return canonical_pairs(gen.TASK_ID, root=REPO)


def test_contract_is_rule_pinned_and_only_exact_axes_are_advertised():
    assert gen.RULE_HASH == "a8ddd603c662"
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_targets"}
    assert gen.AXES["grid_h"]["valid"] == "8..12"
    assert gen.AXES["grid_w"]["valid"] == "9..13"
    assert gen.AXES["n_targets"]["valid"] == "1..5"
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 5


def test_canonical_pairs_are_accepted_and_python_mirror_is_exact():
    for pair in _canonical():
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert rule_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("n_targets", [1, 5])
@pytest.mark.parametrize("shape", [(8, 9), (12, 13)])
def test_exact_overrides_are_observable_in_every_band(band, n_targets, shape):
    h, w = shape
    grid = gen.generate(
        71,
        9,
        difficulty=band,
        grid_h=h,
        grid_w=w,
        n_targets=n_targets,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "grid_h": h,
        "grid_w": w,
        "n_targets": n_targets,
    }
    assert len(true_centers(grid)) == n_targets


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 1},
        {"grid_h": 7},
        {"grid_h": 13},
        {"grid_w": 8},
        {"grid_w": 14},
        {"n_targets": 0},
        {"n_targets": 6},
        {"grid_h": True},
        {"grid_w": "10"},
        {"n_targets": 2.0},
    ],
)
def test_invalid_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize("profile_index", range(5))
@pytest.mark.parametrize("n_targets", [1, 5])
def test_exact_target_override_is_constructive_in_every_scheduled_profile(profile_index, n_targets):
    grid = gen.generate(907, profile_index, grid_h=8, grid_w=9, n_targets=n_targets)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "grid_h": 8, "grid_w": 9, "n_targets": n_targets
    }


@pytest.mark.parametrize("difficulty", ["trivial", 0.5, False])
def test_invalid_difficulty_is_rejected(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty=difficulty)


def test_five_example_schedule_covers_every_teaching_profile_at_every_start():
    assert set(gen.SCHEDULE_PROFILES) == {
        "sparse",
        "shared",
        "boundary",
        "three_arm",
        "diagonal",
    }
    for band in (None, "easy", "medium", "hard"):
        for seed in (0, 19, 2**31 - 1):
            for start in range(20):
                profiles = {
                    gen.schedule_profile(seed, start + offset, difficulty=band)
                    for offset in range(gen.EXAMPLES_NEEDED)
                }
                assert profiles == set(gen.SCHEDULE_PROFILES)


def test_diagonal_overgeneralization_is_a_real_canonical_shortcut_with_generated_refutation():
    shortcut = gen.CANONICAL_SHORTCUTS["cardinal_or_diagonal"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in _canonical())
    grid = gen.generate(101, 4, difficulty="medium")
    assert gen.SEMANTIC_WITNESSES["diagonal_decoy"](grid)
    assert shortcut(grid) != gen.rule_mirror(grid)


def test_each_semantic_profile_materializes_its_promised_counterexample():
    expected = {
        "shared": ("shared_arm_targets", "separated_targets_only"),
        "boundary": ("boundary_target", "margin_two_only"),
        "three_arm": ("three_arm_decoy", "at_least_three_arms"),
        "diagonal": ("diagonal_decoy", "cardinal_or_diagonal"),
    }
    for index in range(gen.EXAMPLES_NEEDED):
        profile = gen.schedule_profile(101, index, difficulty="medium")
        grid = gen.generate(101, index, difficulty="medium")
        assert gen.self_check(grid) == []
        assert gen.rule_mirror(grid) == rule_output(grid)
        if profile in expected:
            witness, rival = expected[profile]
            assert WITNESSES[witness](grid)
            assert gen.SEMANTIC_WITNESSES[witness](grid)
            assert RIVALS[rival](grid) != rule_output(grid)
            assert gen.SEMANTIC_RIVALS[rival](grid) != gen.rule_mirror(grid)


def test_every_consecutive_five_pair_lesson_refutes_all_declared_competitors():
    for band in ("easy", "medium", "hard"):
        for start in range(15):
            pairs = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                index = start + offset
                grid = gen.generate(4301, index, difficulty=band)
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            demos, query = pairs[: gen.EXAMPLES_NEEDED], pairs[-1]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_every_query_rotation_of_six_consecutive_pairs_stays_identifiable():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                index = start + offset
                grid = gen.generate(8117, index, difficulty=band)
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert gen.lesson_identifiable(demos, query) == [], (
                    band, start, query_index, gen.lesson_identifiable(demos, query)
                )


def test_default_distribution_is_deterministic_lawful_varied_and_canonical_scale():
    for band in ("easy", "medium", "hard"):
        grids: set[tuple[tuple[int, ...], ...]] = set()
        target_counts: set[int] = set()
        shapes: set[tuple[int, int]] = set()
        profiles: set[str] = set()
        witness_hits = {name: 0 for name in WITNESSES}
        canonical_scale = 0
        for index in range(50):
            seed = 500 + index
            grid = gen.generate(seed, index, difficulty=band)
            assert grid == gen.generate(seed, index, difficulty=band)
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            assert gen.rule_mirror(grid) == rule_output(grid)
            assert 8 not in {value for row in grid for value in row}
            components = distractor_components(grid)
            assert len(components) == 2
            assert all(3 <= len(component) <= 4 for component in components)
            assert all(len({value for _, _, value in component}) == 1 for component in components)

            obs = gen.observe_overrides(grid)
            target_counts.add(obs["n_targets"])
            shapes.add((obs["grid_h"], obs["grid_w"]))
            profiles.add(gen.schedule_profile(seed, index, difficulty=band))
            canonical_scale += 8 <= len(grid) <= 11 and 10 <= len(grid[0]) <= 12
            for name, witness in WITNESSES.items():
                witness_hits[name] += int(witness(grid))
            grids.add(tuple(map(tuple, grid)))

        assert target_counts == {2, 3, 5}
        assert profiles == set(gen.SCHEDULE_PROFILES)
        assert len(shapes) >= 4
        assert len(grids) >= 45
        assert canonical_scale >= 30
        assert all(hits >= 8 for hits in witness_hits.values())


def test_self_check_rejects_minimal_destructive_impostors():
    grid = gen.generate(891, 2, difficulty="medium")
    assert gen.self_check(grid) == []

    blank = [[0 for _ in row] for row in grid]
    assert gen.self_check(blank)

    alien = [row[:] for row in grid]
    alien[0][0] = 9
    assert gen.self_check(alien)

    no_distractors = [
        [0 if value in (6, 7) else value for value in row]
        for row in grid
    ]
    assert gen.self_check(no_distractors)

    no_targets = [row[:] for row in grid]
    for r, c in true_centers(grid):
        no_targets[r - 1][c] = 0
    assert gen.self_check(no_targets)


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[9] * 10 for _ in range(8)]],
)
def test_malformed_grids_are_diagnostic_not_exceptions(grid):
    assert gen.self_check(grid)
