"""Focused native-parametric contract tests for 2e9bbcd910a7."""
from __future__ import annotations

import copy
import importlib.util
import json
import random
from pathlib import Path

import pytest

from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "2e9bbcd910a7"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator(TASK_ID, root=ROOT)


def _load_prototype():
    path = HERE / "prototype.py"
    assert path.is_file(), "prototype.py has not been implemented"
    spec = importlib.util.spec_from_file_location("_test_2e9b_parametric", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    rows = [
        json.loads(line)
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    ]
    assert len(rows) == 1
    return rows[0]["program_solution"]


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def _grid_key(grid):
    return tuple(tuple(row) for row in grid)


def test_program_contract_preserves_exact_canonical_and_rejects_invalid_settings():
    proto = _load_prototype()
    assert proto.program({"paint_target": "winner"}) == _canonical_program()
    assert proto.program({"paint_target": "crossing_follower"}) != _canonical_program()
    for bad in ({}, {"paint_target": "other"}, {"paint_target": "winner", "extra": 1}):
        with pytest.raises(ValueError):
            proto.program(bad)


@pytest.mark.parametrize("demos,queries", [(2, 1), (3, 4), (6, 4)])
def test_generate_honors_independent_counts_distinct_inputs_and_matched_grammar(demos, queries):
    proto = _load_prototype()
    winner = proto.generate(23, {"paint_target": "winner"}, demos, queries)
    follower = proto.generate(23, {"paint_target": "crossing_follower"}, demos, queries)
    assert len(winner["train"]) == len(follower["train"]) == demos
    assert len(winner["test"]) == len(follower["test"]) == queries
    assert winner["program_solution"] == proto.program({"paint_target": "winner"})
    assert follower["program_solution"] == proto.program({"paint_target": "crossing_follower"})
    assert [_grid_key(g) for g in _inputs(winner)] == [_grid_key(g) for g in _inputs(follower)]
    assert len({_grid_key(g) for g in _inputs(winner)}) == demos + queries
    for episode, setting in (
        (winner, {"paint_target": "winner"}),
        (follower, {"paint_target": "crossing_follower"}),
    ):
        for pair in episode["train"] + episode["test"]:
            assert (len(pair["input"]), len(pair["input"][0])) == (10, 10)
            assert GEN.self_check(pair["input"]) == []
            assert pair["output"] == proto.solve_python(pair["input"], setting)
    assert all(
        a["output"] != b["output"]
        for split in ("train", "test")
        for a, b in zip(winner[split], follower[split])
    )


def test_six_template_lesson_covers_lengths_directions_and_refutes_shortcuts():
    proto = _load_prototype()
    episode = proto.generate(0, {"paint_target": "crossing_follower"}, 2, 4)
    lengths = set()
    directions = set()
    for grid in _inputs(episode):
        ranked = GEN._ranked_runs(grid)
        winner = ranked[0]
        follower = proto.select_crossing_follower(grid)
        lengths.add(len(winner["cells"]))
        directions.add(winner["direction"])
        assert winner["direction"] != follower["direction"]
        assert len(follower["cells"]) < len(winner["cells"])
        assert set(winner["cells"]) & set(follower["cells"])
        assert follower["cells"] != ranked[1]["cells"]
        opposite = [
            run for run in ranked
            if run["direction"] != winner["direction"]
            and len(run["cells"]) < len(winner["cells"])
        ]
        assert opposite[0]["cells"] != follower["cells"]
    assert lengths == {6, 7, 8}
    assert directions == {"se", "sw"}


def test_replay_is_deterministic_fresh_and_global_rng_isolated():
    proto = _load_prototype()
    random.seed(20261024)
    state = random.getstate()
    first = proto.generate(91, {"paint_target": "crossing_follower"}, 3, 4)
    assert random.getstate() == state
    second = proto.generate(91, {"paint_target": "crossing_follower"}, 3, 4)
    assert first == second
    assert first is not second
    before = copy.deepcopy(first)
    first["train"][0]["input"][0][0] = 9
    assert second == before


@pytest.mark.parametrize(
    "demos,queries",
    [(1, 4), (7, 4), (2, 0), (2, 5), (True, 4), (2, False)],
)
def test_count_boundaries_reject_loudly(demos, queries):
    proto = _load_prototype()
    with pytest.raises(ValueError):
        proto.generate(0, {"paint_target": "winner"}, demos, queries)


def test_bounded_audit_rejects_declared_shortcuts():
    path = HERE / "audit_parametric.py"
    assert path.is_file(), "audit_parametric.py has not been implemented"
    spec = importlib.util.spec_from_file_location("_test_2e9b_audit", path)
    assert spec and spec.loader
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    report = audit.run_audit(seeds=(0, 17), demos=3, queries=4)
    assert report["episodes"] == 4
    assert report["pairs"] == 28
    assert report["settings"]["winner"]["crossing_follower_mismatches"] == 14
    follower = report["settings"]["crossing_follower"]
    assert follower["winner_mismatches"] == 14
    assert follower["global_runner_up_mismatches"] == 14
    assert follower["opposite_champion_mismatches"] == 14


def test_public_projection_hides_private_fields_and_controller_turns_are_prefix_safe():
    proto = _load_prototype()
    setting = {"paint_target": "crossing_follower"}
    episode = proto.generate(41, setting, 3, 4)
    public = proto.public_challenge(episode)

    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3
    assert len(public["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert public_challenge_id(public) == public_challenge_id(episode)
    assert public_challenge_bytes(public) == public_challenge_bytes(episode)

    changed_private = copy.deepcopy(episode)
    changed_private["program_solution"] = "private program changed"
    changed_private["settings"] = {"private": True}
    changed_private["seed"] = 999999
    for pair in changed_private["test"]:
        pair["output"] = [[9]]
    assert proto.public_challenge(changed_private) == public
    assert public_challenge_bytes(proto.public_challenge(changed_private)) == public_challenge_bytes(public)

    turns = proto.controller_turns(episode)
    assert len(turns) == 4
    assert all(turn["train"] == public["train"] for turn in turns)
    assert all(len(turn["test"]) == 1 and set(turn["test"][0]) == {"input"} for turn in turns)
    assert turns[0] == proto.public_turn(episode, 0)

    single = proto.generate(41, setting, 3, 1)
    assert public_challenge_bytes(turns[0]) == public_challenge_bytes(proto.public_challenge(single))
    with pytest.raises(IndexError):
        proto.public_turn(episode, 4)
