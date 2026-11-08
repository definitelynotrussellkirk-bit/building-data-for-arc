"""Focused contracts for the separate stop-short prototype (not approval)."""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root, public_challenge_bytes

ROOT = find_root(__file__)
HOME = ROOT / "generators/49c16a3506ab/workspace/parametric"


@pytest.fixture(scope="module")
def family():
    path = HOME / "adapter.py"
    assert path.is_file(), "The stop-short adapter has not been implemented"
    spec = importlib.util.spec_from_file_location("test_stop_short_adapter", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def hand_grid(scatter):
    grid = [[6] * 9 for _ in range(9)]
    for r in range(3):
        for c in range(3):
            grid[r][c] = 2
            grid[r + 6][c + 6] = 4
    for r, c, color in scatter:
        grid[r][c] = color
    return grid


@pytest.mark.parametrize("stop, destinations", [
    (0, [(1, 3, 2), (3, 1, 2), (3, 3, 2), (0, 3, 2), (5, 6, 4)]),
    (1, [(1, 4, 2), (4, 1, 2), (4, 4, 2), (1, 4, 2), (4, 5, 4)]),
    (2, [(1, 5, 2), (5, 1, 2), (5, 5, 2), (2, 5, 2), (3, 4, 4)]),
])
def test_literal_three_branches_and_edge_terminal(family, stop, destinations):
    # Hand-derived endpoints include a diagonal ray that exits beside the block.
    grid = hand_grid([(1, 7, 2), (7, 1, 2), (5, 5, 2), (4, 7, 2), (3, 4, 4)])
    before = copy.deepcopy(grid)
    assert family.transform(grid, stop) == hand_grid(destinations)
    assert grid == before


@pytest.mark.parametrize("stop", [1, 2])
def test_short_paths_stay_at_source_instead_of_reversing(family, stop):
    grid = hand_grid([(1, 4, 2), (4, 7, 4)])
    want = hand_grid([(1, 4, 2), (5 - min(stop, 1), 7, 4)])
    assert family.transform(grid, stop) == want


def test_default_program_and_canonical_labels_are_unchanged(family):
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()
            if json.loads(line).get("task_id") == "49c16a3506ab"]
    assert {row["program_solution"] for row in rows} == {family.program({"stop_short": 0})}
    for pair in canonical_pairs("49c16a3506ab", root=ROOT, labeled_only=True):
        assert family.transform(pair["input"], 0) == pair["output"]


@pytest.mark.parametrize("demos", [2, 3, 4, 5, 6])
def test_counts_matched_inputs_and_demo_only_teaching(family, demos):
    episodes = [family.generate(701 + demos, {"stop_short": s}, demos, 4) for s in range(3)]
    inputs = [[p["input"] for split in ("train", "test") for p in e[split]] for e in episodes]
    assert inputs[0] == inputs[1] == inputs[2]
    assert len({json.dumps(g) for g in inputs[0]}) == demos + 4
    assert [(len(p["input"]), len(p["input"][0])) for p in episodes[0]["test"]] == [
        (9, 9), (15, 21), (30, 30), (21, 30)]
    for s, episode in enumerate(episodes):
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        certificate = family.lesson_certificate(episode["train"], [p["input"] for p in episode["test"]])
        assert certificate["surviving_settings"] == [{"stop_short": s}]
        assert certificate["ambiguous_queries"] == []
        assert certificate["surviving_shortcuts"] == []
        assert all(not family.validate_input(g) for g in inputs[s])


@pytest.mark.parametrize("field,value", [("demos", 1), ("demos", 7), ("demos", True),
    ("queries", 0), ("queries", 5), ("queries", 2.0), ("seed", -1), ("seed", True)])
def test_request_boundaries_reject_instead_of_truncating(family, field, value):
    args = {"seed": 17, "settings": {"stop_short": 0}, "demos": 3, "queries": 4}
    args[field] = value
    with pytest.raises(ValueError):
        family.generate(**args)


@pytest.mark.parametrize("settings", [{}, {"stop_short": True}, {"stop_short": 1.0},
    {"stop_short": -1}, {"stop_short": 3}, {"stop_short": 0, "secret": 2}])
def test_settings_reject_wrong_types_and_unknown_parameters(family, settings):
    with pytest.raises(ValueError):
        family.program(settings)


def test_query_prefix_and_public_projection_ignore_private_fields(family):
    one = family.generate(31, {"stop_short": 2}, 3, 1)
    four = family.generate(31, {"stop_short": 2}, 3, 4)
    assert one["train"] == four["train"]
    assert one["test"][0] == four["test"][0]
    assert family.visible_turn(one, 0) == family.visible_turn(four, 0)
    for index in range(4):
        visible = family.visible_turn(four, index)
        assert set(visible) == {"train", "test"}
        assert len(visible["test"]) == 1
        assert set(visible["test"][0]) == {"input"}
    with pytest.raises(ValueError):
        family.visible_turn(four, True)
    changed = copy.deepcopy(four)
    changed["settings"] = {"stop_short": 999}
    changed["seed"] = 9000
    changed["program_solution"] = "PRIVATE"
    changed["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(changed) == public_challenge_bytes(four)


def test_certificate_rejects_inconsistent_demos_and_ignores_query_answers(family):
    episode = family.generate(42, {"stop_short": 1}, 2, 4)
    bad = copy.deepcopy(episode["train"])
    bad[0]["output"][0][0] = (bad[0]["output"][0][0] + 1) % 10
    with pytest.raises(ValueError, match="demonstrations"):
        family.lesson_certificate(bad, [p["input"] for p in episode["test"]])
