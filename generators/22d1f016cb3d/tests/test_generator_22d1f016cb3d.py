from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, load_selected_generator


TASK = "22d1f016cb3d"
ROOT = find_root(__file__)
MODULE, MODULE_PATH, MODULE_SHA256 = load_selected_generator(TASK, root=ROOT)


def _canonical_row():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        return next(row for row in map(json.loads, handle) if row.get("task_id") == TASK)


def _frozen(grid):
    return tuple(map(tuple, grid))


def test_rule_hash_matches_canonical_program():
    rule = " ".join(_canonical_row()["program_solution"].split())
    assert MODULE.RULE_HASH == hashlib.sha256(rule.encode()).hexdigest()[:12]


def test_every_public_profile_replays_its_canonical_pair_exactly():
    pairs = _canonical_row()["train"] + _canonical_row()["test"]
    assert len(pairs) == len(MODULE.PUBLIC_PROFILES) == 3
    for profile, pair in zip(MODULE.PUBLIC_PROFILES, pairs):
        grid = MODULE.generate(0, 0, scene_profile=profile)
        assert grid == pair["input"]
        assert MODULE.rule_mirror(grid) == pair["output"]
        assert MODULE.canonical_profile_signature(grid) == profile
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


def test_every_general_profile_is_valid_and_recoverable_in_every_band():
    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        for profile_index, profile in enumerate(MODULE.GENERAL_PROFILES):
            for seed in range(30):
                grid = MODULE.generate(
                    100_000 * band_index + 1_000 * profile_index + seed,
                    seed * 31,
                    difficulty=band,
                    scene_profile=profile,
                )
                analysis = MODULE._analysis(grid)
                assert not analysis["errors"]
                assert analysis["scene_profile"] == profile
                assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


def test_default_generation_reaches_every_profile():
    seen = {
        MODULE.observe_overrides(MODULE.generate(seed, seed * 37))["scene_profile"]
        for seed in range(3000)
    }
    assert seen == set(MODULE.SCENE_PROFILES)


def test_solid_rectangle_has_corner_edge_and_interior_zones():
    grid = [[0] * 7 for _ in range(7)]
    for row in range(1, 6):
        for col in range(1, 6):
            grid[row][col] = 5
    output = MODULE.rule_mirror(grid)
    counts = {color: sum(value == color for row in output for value in row) for color in (1, 2, 4)}
    assert counts == {1: 4, 2: 9, 4: 12}


def test_thin_line_uses_ends_and_edges_without_interior_color():
    grid = [[0] * 8 for _ in range(3)]
    grid[1][1:7] = [5] * 6
    output = MODULE.rule_mirror(grid)
    assert output[1] == [0, 1, 4, 4, 4, 4, 1, 0]
    assert all(2 not in row for row in output)


def test_rule_preserves_every_nonfive_value_even_reserved_output_colors():
    grid = [
        [0, 1, 2, 3, 4],
        [6, 5, 5, 5, 7],
        [8, 5, 5, 5, 9],
        [0, 5, 5, 5, 0],
        [1, 2, 3, 4, 6],
    ]
    output = MODULE.rule_mirror(grid)
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] != 5:
                assert output[row][col] == grid[row][col]


def test_irregular_profiles_exercise_local_not_bbox_logic():
    for profile in ("hollow_frame", "punctured_rectangle", "orthogonal_shape", "mixed_shapes"):
        grid = MODULE.generate(123, 456, scene_profile=profile)
        facts = MODULE._analysis(grid)["facts"]
        assert any(not component["solid"] for component in facts["components"])
        assert MODULE.rule_mirror(grid) == facts["output"]


def test_generation_is_deterministic_fresh_and_global_rng_independent():
    random.seed(987654)
    before = random.getstate()
    first = MODULE.generate(111, 222, difficulty="hard")
    assert random.getstate() == before
    second = MODULE.generate(111, 222, difficulty="hard")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert MODULE.generate(111, 222, difficulty="hard") == second


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[5, 5], [5]],
        [[True] * 3 for _ in range(3)],
        [[10] * 3 for _ in range(3)],
        [[0] * 3 for _ in range(3)],
        [[1, 5, 0], [0, 5, 0], [0, 5, 0]],
    ],
)
def test_self_check_rejects_malformed_or_undeclared_training_scenes(grid):
    assert MODULE.self_check(grid)


def test_unknown_difficulty_profile_and_axis_fail_closed():
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, difficulty="extreme")
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, scene_profile="not_real")
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, grid_h=10)


def test_public_returns_are_fresh():
    first = MODULE.generate(1, 2, scene_profile="public_1")
    frozen = _frozen(first)
    first[0][0] = 0
    assert _frozen(MODULE.generate(1, 2, scene_profile="public_1")) == frozen


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_integer_seed_scalars(bad_seed):
    with pytest.raises((TypeError, ValueError), match="seed"):
        MODULE.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1", -1])
def test_generate_rejects_invalid_sample_index_scalars(bad_index):
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        MODULE.generate(0, bad_index)


def _is_exact_canonical_profile(grid):
    return (
        len(grid) == 10
        and len(grid[0]) == 10
        and len({value for row in grid for value in row}) == 2
    )


def test_default_generation_clears_canonical_profile_floor_in_every_band():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        exact = sum(
            _is_exact_canonical_profile(
                MODULE.generate(
                    70_000 + 10_000 * band_index + sample_index,
                    sample_index,
                    difficulty=band,
                )
            )
            for sample_index in range(120)
        )
        assert exact >= 30, (band, exact)


def _straight_segment_witness():
    grid = [[0] * 7 for _ in range(7)]
    for row in range(1, 6):
        for col in range(1, 6):
            if row in {1, 5} or col in {1, 5}:
                grid[row][col] = 5
    return grid


def test_semantic_degree_shortcut_fits_canonical_but_fails_straight_segments():
    witness = _straight_segment_witness()
    assert MODULE.strict_canonical_like(witness) == []
    shortcut = MODULE.SEMANTIC_RIVALS["neighbor_degree_zones"]
    for pair in _canonical_row()["train"] + _canonical_row()["test"]:
        assert shortcut(pair["input"]) == pair["output"]
    assert MODULE.SEMANTIC_WITNESSES["straight_degree_two"](witness)
    assert shortcut(witness) != MODULE.rule_mirror(witness)
    assert "neighbor_degree_zones" in MODULE.WITNESS_RIVALS["straight_degree_two"]
    assert MODULE.CANONICAL_SHORTCUTS["neighbor_degree_zones"] is shortcut


def test_every_lawful_scene_refutes_edge_collapse_lesson_competitor():
    rival = MODULE.LESSON_COMPETITORS["collapse_edges_to_ends"]
    for profile_index, profile in enumerate(MODULE.SCENE_PROFILES):
        grid = MODULE.generate(
            900_000 + profile_index,
            profile_index,
            difficulty="medium",
            scene_profile=profile,
        )
        assert MODULE.self_check(grid) == []
        assert MODULE.SEMANTIC_WITNESSES["edge_classification"](grid)
        assert rival(grid) != MODULE.rule_mirror(grid)

@pytest.mark.parametrize(
    "zero_cells",
    [
        [(5, 5)],
        [(row, col) for row in range(2) for col in range(2)],
        [(5, col) for col in range(4)],
    ],
    ids=("singleton-hole", "solid-2x2-hole", "short-line-hole"),
)
def test_self_check_rejects_modal_foreground_minimal_impostors(zero_cells):
    grid = [[5] * 10 for _ in range(10)]
    for row, col in zero_cells:
        grid[row][col] = 0
    assert MODULE.self_check(grid)


def _labeled_pair(seed, sample_index, profile):
    grid = MODULE.generate(
        seed,
        sample_index,
        difficulty="medium",
        scene_profile=profile,
    )
    return {"input": grid, "output": MODULE.rule_mirror(grid)}


def test_lesson_identifiable_accepts_every_rotation_of_default_period():
    pairs = [
        {
            "input": MODULE.generate(12345, index, difficulty="medium"),
            "output": MODULE.rule_mirror(
                MODULE.generate(12345, index, difficulty="medium")
            ),
        }
        for index in range(MODULE.LESSON_SCHEDULE_PERIOD)
    ]
    for query_index, query in enumerate(pairs):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert MODULE.lesson_identifiable(demos, query) == []


def test_lesson_identifiable_reports_canonical_fitting_rival_when_unrefuted():
    demos = [
        _labeled_pair(500 + index, index, profile)
        for index, profile in enumerate(MODULE.PUBLIC_PROFILES)
    ]
    query = _labeled_pair(900, 0, "hollow_frame")
    reasons = MODULE.lesson_identifiable(demos, query)
    assert any("neighbor_degree_zones" in reason for reason in reasons)

@pytest.mark.parametrize(
    ("seed", "start_index"),
    [
        (2648124371, 17),
        (3217940425, 24),
        (4234532217, 33),
    ],
)
def test_default_schedule_survives_materializer_duplicate_filter(seed, start_index):
    pairs = []
    seen = set()
    for sample_index in range(start_index, start_index + 16):
        grid = MODULE.generate(seed, sample_index, difficulty="easy")
        frozen = _frozen(grid)
        if frozen in seen:
            continue
        seen.add(frozen)
        pairs.append({"input": grid, "output": MODULE.rule_mirror(grid)})
        if len(pairs) == 4:
            break
    assert len(pairs) == 4
    for query_index, query in enumerate(pairs):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert MODULE.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize(
    ("band", "seed", "start_index"),
    [
        ("easy", 209885690409717, 0),
        ("medium", 101493307012095, 0),
        ("medium", 141435715218674, 11),
        ("hard", 83689609006155, 0),
        ("hard", 150128558633518, 11),
    ],
)
def test_default_schedule_refutes_generic_object_selection_in_every_rotation(
    band, seed, start_index
):
    from review_diagnostics import search_lesson

    pairs = []
    seen = set()
    for sample_index in range(start_index, start_index + 64):
        grid = MODULE.generate(seed, sample_index, difficulty=band)
        frozen = _frozen(grid)
        if frozen in seen:
            continue
        seen.add(frozen)
        pairs.append({"input": grid, "output": MODULE.rule_mirror(grid)})
        if len(pairs) == 4:
            break

    assert len(pairs) == 4
    for query_index, query in enumerate(pairs):
        instance = {
            "train": [pair for index, pair in enumerate(pairs) if index != query_index],
            "test": [query],
        }
        searched = search_lesson(MODULE, instance)
        assert not searched["ambiguous"], (
            band,
            seed,
            start_index,
            query_index,
            [
                name
                for name, row in searched["candidates"].items()
                if row.get("status") == "ambiguous"
            ],
        )
