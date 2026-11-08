"""Focused tests for the proposed priority prototype, not production approval."""
from __future__ import annotations

import importlib.util
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
GENERATOR, GENERATOR_PATH, _ = load_selected_generator("ed860c0a9107", root=ROOT)


@pytest.fixture(scope="module")
def prototype():
    # The task-test runtime mirrors the task workspace beside these tests.
    path = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"
    assert path.is_file(), "the requested task-local parametric prototype is missing"
    spec = importlib.util.spec_from_file_location("ed860c0a9107_priority_prototype", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bridge():
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(timeout=10.0) as value:
        yield value


@pytest.fixture(scope="module")
def episodes(prototype, bridge):
    return {
        priority: prototype.generate_episode(
            20261020, priority=priority, root=ROOT, bridge=bridge
        )
        for priority in ("first", "last")
    }


def test_default_program_is_the_exact_canonical_authority(prototype):
    assert prototype.DEFAULT_PRIORITY == "first"
    assert prototype.PRIORITIES == ("first", "last")
    assert prototype.materialize_rule(root=ROOT) == prototype.canonical_rule(ROOT)


def test_unknown_priorities_and_noninteger_seeds_fail_closed(prototype):
    for priority in ("middle", "", None, 0):
        with pytest.raises((TypeError, ValueError), match="priority"):
            prototype.select_priority(10, priority)
    for seed in (True, 1.5, "10"):
        with pytest.raises(TypeError, match="seed"):
            prototype.select_priority(seed, "sample")


def test_seeded_parameter_is_repeatable_and_global_rng_pure(prototype):
    random.seed(20261020)
    state = random.getstate()
    selected = [prototype.select_priority(seed, "sample") for seed in range(16)]
    assert random.getstate() == state
    assert set(selected) == {"first", "last"}
    assert selected == [prototype.select_priority(seed, "sample") for seed in range(16)]


def test_default_racket_reproduces_all_eight_canonical_labels(prototype, bridge):
    pairs = canonical_pairs("ed860c0a9107", root=ROOT, labeled_only=True)
    assert len(pairs) == 8
    program = prototype.materialize_rule(root=ROOT)
    for pair in pairs:
        assert prototype.apply_rule(bridge, program, pair["input"]) == pair["output"]


def test_lawful_conflict_has_two_independently_known_racket_answers(prototype, bridge):
    grid = [[9] * 14 for _ in range(14)]
    for top, left, color in ((2, 2, 1), (8, 8, 2)):
        for row in range(2):
            for col in range(2):
                grid[top + row][left + col] = color if row == col == 0 else 0
    assert GENERATOR.self_check(grid) == []
    assert prototype.apply_rule(
        bridge, prototype.materialize_rule("first", root=ROOT), grid
    ) == [[1, 0], [0, 0]]
    assert prototype.apply_rule(
        bridge, prototype.materialize_rule("last", root=ROOT), grid
    ) == [[2, 0], [0, 0]]


@pytest.mark.parametrize("priority", ("first", "last"))
def test_complete_episode_and_every_query_role_rotation_identify_priority(episodes, priority):
    episode = episodes[priority]
    assert episode["parameters"] == {"priority": priority}
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 1
    pairs = episode["train"] + episode["test"]
    for index, pair in enumerate(pairs):
        assert pair["output"] == episode["parameter_predictions"][priority][index]
        assert GENERATOR.self_check(pair["input"]) == []
    assert len(episode["role_rotations"]) == 4
    assert all(row["consistent_priorities"] == [priority] for row in episode["role_rotations"])
    assert all(row["refuted_priorities"] for row in episode["role_rotations"])


def test_changing_priority_changes_labels_without_resampling_inputs(episodes):
    first = episodes["first"]["train"] + episodes["first"]["test"]
    last = episodes["last"]["train"] + episodes["last"]["test"]
    assert [pair["input"] for pair in first] == [pair["input"] for pair in last]
    assert all(a["output"] != b["output"] for a, b in zip(first, last))


def test_parameter_is_selected_once_for_the_whole_episode(prototype, bridge):
    episode = prototype.generate_episode(29, priority="sample", root=ROOT, bridge=bridge)
    selected = prototype.select_priority(29, "sample")
    assert episode["parameters"] == {"priority": selected}
    assert episode["program"] == prototype.materialize_rule(selected, root=ROOT)
    assert [pair["output"] for pair in episode["train"] + episode["test"]] == episode["parameter_predictions"][selected]


def test_visible_challenge_has_only_demonstrations_and_unlabeled_queries(prototype, episodes):
    episode = episodes["last"]
    visible = prototype.public_challenge(episode)
    assert set(visible) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in visible["train"])
    assert all(set(pair) == {"input"} for pair in visible["test"])
    original = episode["train"][0]["input"][0][0]
    visible["train"][0]["input"][0][0] = (original + 1) % 10
    assert episode["train"][0]["input"][0][0] == original


def test_canonical_only_lesson_is_honestly_reported_as_ambiguous(prototype, bridge):
    pairs = canonical_pairs("ed860c0a9107", root=ROOT, labeled_only=True)[:4]
    predictions = {
        priority: [
            prototype.apply_rule(bridge, prototype.materialize_rule(priority, root=ROOT), pair["input"])
            for pair in pairs
        ]
        for priority in ("first", "last")
    }
    rotations = prototype.assess_role_rotations(pairs, predictions)
    assert len(rotations) == 4
    assert all(row["consistent_priorities"] == ["first", "last"] for row in rotations)


def test_prediction_count_mismatch_is_not_silently_truncated(prototype):
    with pytest.raises(ValueError, match="prediction count"):
        prototype.assess_role_rotations(
            [{"input": [[0]], "output": [[0]]}] * 4,
            {"first": [[[0]]] * 4, "last": [[[0]]] * 3},
        )


def test_spatial_rotation_reexecutes_priority_in_rotated_row_major_order(prototype, bridge):
    grid = [[9] * 14 for _ in range(14)]
    for top, left, color in ((2, 2, 1), (8, 8, 2)):
        for row in range(2):
            for col in range(2):
                grid[top + row][left + col] = color if row == col == 0 else 0
    first_program = prototype.materialize_rule("first", root=ROOT)
    last_program = prototype.materialize_rule("last", root=ROOT)
    for turns in range(4):
        rotated = prototype.rotate_grid(grid, turns)
        assert GENERATOR.self_check(rotated) == []
        first = prototype.apply_rule(bridge, first_program, rotated)
        last = prototype.apply_rule(bridge, last_program, rotated)
        assert first != last
    original_output = prototype.apply_rule(bridge, first_program, grid)
    rotated_output = prototype.apply_rule(bridge, first_program, prototype.rotate_grid(grid, 2))
    assert rotated_output != prototype.rotate_grid(original_output, 2)


def test_episode_generation_is_repeatable_without_global_rng_changes(prototype, episodes, bridge):
    state = random.getstate()
    repeat = prototype.generate_episode(20261020, priority="last", root=ROOT, bridge=bridge)
    assert random.getstate() == state
    assert repeat == episodes["last"]
