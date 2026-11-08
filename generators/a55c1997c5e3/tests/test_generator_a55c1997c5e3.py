from __future__ import annotations

import copy
import random

import numpy as np
import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "a55c1997c5e3"
ROOT = find_root(__file__)
gen, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def test_all_canonical_inputs_are_accepted_and_mirror_outputs():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen._official_python_mirror(pair["input"]) == pair["output"]


def test_production_schedule_is_observable_for_its_complete_period():
    assert len(set(gen.SCENE_PROFILES)) == 6
    assert len(gen.SCHEDULE_PROFILES) == gen.LESSON_SCHEDULE_PERIOD == 10
    assert gen.EXAMPLES_NEEDED == 6
    for index, expected_profile in enumerate(gen.SCHEDULE_PROFILES):
        grid = gen.generate(314159, index, difficulty="medium")
        assert gen.observe_overrides(grid)["scene_profile"] == expected_profile
        assert gen.schedule_profile(314159, index, "medium") == expected_profile
        assert gen.self_check(grid) == []


@pytest.mark.parametrize("profile,predicate", [
    ("longest_over_priority", "_longest_beats_priority"),
    ("tie_right_over_down", "_first_direction_tie"),
    ("tie_down_over_left", "_first_direction_tie"),
    ("deep_lexicographic_tie", "_deep_direction_tie"),
    ("branchy_unique_longest", "_has_off_path_distractor"),
    ("complete_direction_order", "_complete_direction_ties"),
])
def test_explicit_scene_profile_has_its_named_semantic_behavior(profile, predicate):
    grid = gen.generate(314159, 0, difficulty="medium", scene_profile=profile)
    assert gen.observe_overrides(grid)["scene_profile"] == profile
    assert gen.self_check(grid) == []
    assert getattr(gen, predicate)(grid)


def test_exact_overrides_round_trip_at_boundaries():
    for profile in gen.SCENE_PROFILES:
        for h, w in ((16, 18), (28, 30)):
            grid = gen.generate(
                2718,
                11,
                difficulty="easy",
                grid_h=h,
                grid_w=w,
                scene_profile=profile,
            )
            assert gen.observe_overrides(grid) == {
                "grid_h": h,
                "grid_w": w,
                "scene_profile": profile,
            }
            assert gen.self_check(grid) == []


def test_determinism_fresh_objects_and_global_input_purity():
    random.seed(123456)
    np.random.seed(654321)
    python_rng_before = random.getstate()
    numpy_rng_before = np.random.get_state()

    first = gen.generate(99, 4, difficulty="hard")
    snapshot = copy.deepcopy(first)
    second = gen.generate(99, 4, difficulty="hard")

    assert random.getstate() == python_rng_before
    numpy_rng_after = np.random.get_state()
    assert numpy_rng_after[0] == numpy_rng_before[0]
    assert np.array_equal(numpy_rng_after[1], numpy_rng_before[1])
    assert numpy_rng_after[2:] == numpy_rng_before[2:]
    assert first == second
    assert first is not second
    first[0][0] = 9
    assert second == snapshot


def test_self_check_rejects_targeted_impostors():
    base = gen.generate(
        123,
        0,
        grid_h=20,
        grid_w=24,
        scene_profile="branchy_unique_longest",
    )
    nodes, errors = gen._extract_nodes(base)
    assert not errors

    wrong_color = copy.deepcopy(base)
    r, c, _ = nodes[0]
    wrong_color[r][c] = 3

    broken_block = copy.deepcopy(base)
    r, c, _ = nodes[1]
    broken_block[r][c] = 0

    second_start = copy.deepcopy(base)
    r, c, _ = next(node for node in nodes if node[2] == 8)
    for rr in range(r, r + 2):
        for cc in range(c, c + 2):
            second_start[rr][cc] = 2

    corridor_in_input = copy.deepcopy(base)
    analysis = gen._analyze(base)
    a, b = analysis["best_path"][:2]
    gen._paint_edge(corridor_in_input, a, b)

    for impostor in (wrong_color, broken_block, second_start, corridor_in_input):
        assert gen.self_check(impostor), "targeted malformed scene was accepted"


def test_self_check_rejects_touching_nodes_with_invisible_selected_edge():
    grid = [[0] * 12 for _ in range(8)]
    for r, c, color in ((2, 1, 2), (2, 3, 8), (2, 7, 8)):
        for rr in range(r, r + 2):
            for cc in range(c, c + 2):
                grid[rr][cc] = color

    reasons = gen.self_check(grid)
    assert reasons
    assert any("blank corridor" in reason for reason in reasons)


def test_default_demo_count_refutes_named_rivals_with_mirror_pairs():
    # This tests the hook contract with the Python audit mirror. The full gate
    # separately materializes outputs through the canonical Racket oracle.
    pairs = []
    for index in range(gen.EXAMPLES_NEEDED + 1):
        inp = gen.generate(777, index, difficulty="medium")
        pairs.append({"input": inp, "output": gen._official_python_mirror(inp)})
    assert gen.lesson_identifiable(pairs[:gen.EXAMPLES_NEEDED], pairs[gen.EXAMPLES_NEEDED]) == []


def test_declared_witness_rivals_disagree_on_every_explicit_profile_hit():
    for index, expected_profile in enumerate(gen.SCENE_PROFILES):
        grid = gen.generate(4242, index, difficulty="medium", scene_profile=expected_profile)
        authoritative = gen._official_python_mirror(grid)
        assert gen.observe_overrides(grid)["scene_profile"] == expected_profile
        for witness_name, predicate in gen.SEMANTIC_WITNESSES.items():
            if not predicate(grid):
                continue
            rival_names = gen.WITNESS_RIVALS[witness_name]
            assert any(
                gen.SEMANTIC_RIVALS[name](grid) != authoritative
                for name in rival_names
            ), witness_name


@pytest.mark.parametrize("seed", [0, 1, 42, 314159])
@pytest.mark.parametrize("height,width", [(16, 18), (28, 30)])
def test_complete_direction_profile_refutes_all_constant_orders_and_distance(seed, height, width):
    grid = gen.generate(
        seed, 0, difficulty="medium", scene_profile="complete_direction_order",
        grid_h=height, grid_w=width,
    )
    assert gen.self_check(grid) == []
    assert gen._physical_distance_tie(grid)
    authoritative = gen._official_python_mirror(grid)
    # All 4! - 1 nonofficial constant direction orders must be represented.
    assert len(gen._DIRECTION_RIVALS) == 23
    for name, rival in gen._DIRECTION_RIVALS.items():
        assert rival(grid) != authoritative, name


@pytest.mark.parametrize("bad", [
    {"grid_h": 15},
    {"grid_w": 31},
    {"scene_profile": "not-a-profile"},
])
def test_invalid_overrides_reject_loudly(bad):
    with pytest.raises((ValueError, TypeError)):
        gen.generate(1, 0, **bad)
