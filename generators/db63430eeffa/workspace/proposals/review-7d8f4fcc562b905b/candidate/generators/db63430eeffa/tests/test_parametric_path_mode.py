"""Focused tests for the proposed, unselected path-selection prototype."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest

for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import canonical_pairs, find_root  # noqa: E402

TASK_ID = "db63430eeffa"
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"


def prototype():
    assert PROTOTYPE_PATH.is_file(), "the path-selection prototype has not been implemented"
    spec = importlib.util.spec_from_file_location(
        f"parametric_path_mode_{TASK_ID}", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def witness_grid():
    grid = [[0] * 9 for _ in range(9)]
    grid[1][1] = 8
    grid[7][4] = 8
    return grid


def test_default_rule_is_exact_canonical_and_matches_every_labeled_pair():
    proto = prototype()
    assert proto.DEFAULT_PATH_MODE == "both"
    assert proto.PATH_MODES == ("both", "diagonal_first", "straight_first")
    assert proto.exact_program_hash("both") == (
        "738576fedc01cbcd29e0e5a381777ed10929461bca3c60994cee0a3fb4010c46"
    )
    assert proto.normalized_program_hash("both") == (
        "3e3bf77eb552f1b44d376e68304bd479643b4dce5f09e62b73ff0f17a69e083b"
    )
    assert proto.program_for("both") == proto.canonical_source()
    assert proto.program_for("diagonal_first") != proto.program_for("both")
    assert proto.program_for("straight_first") != proto.program_for("both")
    for pair in canonical_pairs(TASK_ID, root=ROOT):
        assert proto.solve(pair["input"], path_mode="both") == pair["output"]


def test_three_path_modes_execute_distinct_nearby_rules_on_one_input():
    proto = prototype()
    grid = witness_grid()
    before = deepcopy(grid)
    outputs = {mode: proto.solve(grid, path_mode=mode) for mode in proto.PATH_MODES}
    assert grid == before
    assert len({tuple(map(tuple, output)) for output in outputs.values()}) == 3

    diagonal = outputs["diagonal_first"]
    straight = outputs["straight_first"]
    both = outputs["both"]
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] == 8:
                assert diagonal[row][col] == straight[row][col] == both[row][col] == 8
            elif diagonal[row][col] == 3 or straight[row][col] == 3:
                assert both[row][col] == 3


@pytest.mark.parametrize("mode", ("both", "diagonal_first", "straight_first"))
def test_episode_has_three_demos_four_distinct_queries_and_identifies_mode(mode):
    proto = prototype()
    episode = proto.generate_episode(17, path_mode=mode, n_train=3, n_test=4)
    assert episode["parameters"] == {"path_mode": mode}
    assert episode["meta"]["n_train"] == 3
    assert episode["meta"]["n_test"] == 4
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4

    pairs = episode["train"] + episode["test"]
    assert len({tuple(map(tuple, pair["input"])) for pair in pairs}) == 7
    for pair in pairs:
        assert pair["output"] == proto.solve(pair["input"], path_mode=mode)
        assert all(
            pair["output"] != proto.solve(pair["input"], path_mode=rival)
            for rival in proto.PATH_MODES
            if rival != mode
        )
    analysis = proto.analyze_episode(episode)
    assert analysis["identified"] is True
    assert analysis["surviving_modes"] == [mode]
    assert analysis["all_queries_distinct"] is True


def test_public_projection_hides_private_setting_program_and_query_answers():
    proto = prototype()
    episode = proto.generate_episode(
        23, path_mode="straight_first", n_train=3, n_test=4
    )
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])

    original_id = proto.public_id(episode)
    changed_private = deepcopy(episode)
    changed_private["parameters"]["path_mode"] = "both"
    changed_private["program"] = "private replacement"
    changed_private["meta"]["seed"] = 999999
    changed_private["test"][0]["output"] = [[9]]
    assert proto.public_id(changed_private) == original_id
    filename = proto.public_filename(episode)
    assert filename == f"challenge-{original_id}.json"
    assert all(mode not in filename for mode in proto.PATH_MODES)
    assert "seed" not in filename


@pytest.mark.parametrize(
    "call",
    [
        lambda proto: proto.solve(witness_grid(), path_mode="sideways"),
        lambda proto: proto.generate_episode(-1),
        lambda proto: proto.generate_episode(1, n_train=0),
        lambda proto: proto.generate_episode(1, n_test=True),
    ],
)
def test_invalid_modes_seeds_and_counts_fail_loudly(call):
    with pytest.raises(ValueError):
        call(prototype())
