from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root


TASK_ID = "d38b0f2356c1"
ROOT = find_root(__file__)
MODULE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"


def load_prototype():
    assert MODULE_PATH.is_file(), "parametric prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("d38_marker_color_test_subject", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()]
    matches = [row["program_solution"] for row in rows if row.get("task_id") == TASK_ID]
    assert len(set(matches)) == 1
    return matches[0]


def test_default_program_is_exact_canonical_authority():
    prototype = load_prototype()
    assert prototype.program({"marker_color": 8}) == canonical_program()


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"marker_color": 7}, {"marker_color": True}, {"marker_color": 8.0},
     {"marker_color": 8, "extra": 1}],
)
def test_program_rejects_invalid_settings(settings):
    prototype = load_prototype()
    with pytest.raises(ValueError):
        prototype.program(settings)

import copy

from reviewer_support import public_challenge_bytes, public_challenge_id


def grid_key(grid):
    return tuple(tuple(row) for row in grid)


def selected_index(grid, marker):
    starts = (0, 4, 8)
    missing = []
    for index in range(9):
        br, bc = starts[index // 3], starts[index % 3]
        block = [row[bc : bc + 3] for row in grid[br : br + 3]]
        if all(value != marker for row in block for value in row):
            missing.append(index)
    assert len(missing) == 1
    return missing[0]


def ambiguous_same_block_input():
    grid = [[0] * 11 for _ in range(11)]
    for sep in (3, 7):
        for col in range(11):
            grid[sep][col] = 5
        for row in range(11):
            grid[row][sep] = 5
    starts = (0, 4, 8)
    for index in range(9):
        br, bc = starts[index // 3], starts[index % 3]
        grid[br + 1][bc + 1] = 2 + (index % 4)
        if index != 0:
            grid[br][bc] = 8
            grid[br][bc + 2] = 9
    return grid


def test_marker_color_selects_different_blocks_on_matched_input():
    prototype = load_prototype()
    grid = prototype.sample_input(17, 0)
    before = copy.deepcopy(grid)
    assert selected_index(grid, 8) != selected_index(grid, 9)
    output8 = prototype.transform(grid, marker_color=8)
    output9 = prototype.transform(grid, marker_color=9)
    assert output8 != output9
    assert grid == before
    assert all(len(row) == 11 for row in output8)


@pytest.mark.parametrize("n_demo", range(2, 7))
@pytest.mark.parametrize("marker", [8, 9])
def test_counts_unique_queries_and_demo_only_teaching(n_demo, marker):
    prototype = load_prototype()
    episode = prototype.sample_episode(23, marker_color=marker, n_demo=n_demo, n_query=4)
    assert len(episode["train"]) == n_demo
    assert len(episode["test"]) == 4
    pairs = episode["train"] + episode["test"]
    assert len({grid_key(pair["input"]) for pair in pairs}) == len(pairs)
    certificate = prototype.lesson_certificate(episode)
    assert certificate["survivors"] == [marker]
    assert certificate["identifiable"] is True
    changed = copy.deepcopy(episode)
    for pair in changed["test"]:
        pair["output"] = [[False]]
    assert prototype.lesson_certificate(changed) == certificate


def test_matched_settings_query_prefix_and_demo_count_independence():
    prototype = load_prototype()
    a = prototype.sample_episode(83, marker_color=8, n_demo=3, n_query=4)
    b = prototype.sample_episode(83, marker_color=9, n_demo=3, n_query=4)
    for split in ("train", "test"):
        assert [pair["input"] for pair in a[split]] == [pair["input"] for pair in b[split]]
    one = prototype.sample_episode(83, marker_color=8, n_demo=3, n_query=1)
    assert a["test"][:1] == one["test"]
    assert prototype.first_turn(a) == prototype.first_turn(one)
    six = prototype.sample_episode(83, marker_color=8, n_demo=6, n_query=4)
    assert a["train"] == six["train"][:3]
    assert a["test"] == six["test"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True}, {"seed": -1},
        {"n_demo": 1}, {"n_demo": 7}, {"n_demo": True}, {"n_demo": 3.0},
        {"n_query": 0}, {"n_query": 5}, {"n_query": False}, {"n_query": 4.0},
        {"marker_color": 7}, {"marker_color": True},
    ],
)
def test_invalid_episode_requests_reject(kwargs):
    prototype = load_prototype()
    request = {"seed": 0, "marker_color": 8, "n_demo": 3, "n_query": 4}
    request.update(kwargs)
    with pytest.raises(ValueError):
        prototype.sample_episode(**request)


def test_fixed_geometry_is_structural_not_padding():
    prototype = load_prototype()
    episode = prototype.sample_episode(101, marker_color=8, n_demo=2, n_query=4)
    for pair in episode["train"] + episode["test"]:
        grid = pair["input"]
        assert (len(grid), len(grid[0])) == (11, 11)
        assert all(grid[3][c] == 5 and grid[7][c] == 5 for c in range(11))
        assert all(grid[r][3] == 5 and grid[r][7] == 5 for r in range(11))
        assert selected_index(grid, 8) != selected_index(grid, 9)


def test_public_identity_and_first_turn_use_visible_bytes_only():
    prototype = load_prototype()
    episode = prototype.sample_episode(91, marker_color=8, n_demo=2, n_query=4)
    changed = copy.deepcopy(episode)
    changed.update(seed=999, parameters={"marker_color": 9}, program="secret")
    for pair in changed["test"]:
        pair["output"] = [[9]]
    assert public_challenge_id(episode) == public_challenge_id(changed)
    assert public_challenge_bytes(episode) == public_challenge_bytes(changed)
    public = json.loads(public_challenge_bytes(episode))
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert len(prototype.first_turn(episode)["test"]) == 1


def test_ambiguous_demos_cannot_borrow_query_answers():
    prototype = load_prototype()
    grid = ambiguous_same_block_input()
    demo = {"input": grid, "output": prototype.transform(grid, marker_color=8)}
    query = prototype.sample_input(9, 1)
    episode = {
        "train": [copy.deepcopy(demo), copy.deepcopy(demo)],
        "test": [{"input": query, "output": prototype.transform(query, marker_color=8)}],
    }
    certificate = prototype.lesson_certificate(episode)
    assert certificate["survivors"] == [8, 9]
    assert certificate["identifiable"] is False
    assert certificate["query_agreement"] == [False]


def test_racket_labels_export_replay_and_tamper_rejection(tmp_path):
    prototype = load_prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(timeout=15) as bridge:
        episodes = [
            prototype.generate_episode(17, marker_color=marker, n_demo=2, n_query=4, bridge=bridge)
            for marker in (8, 9)
        ]
        output = tmp_path / "batch"
        index = prototype.write_batch(episodes, output)
        result = prototype.verify_batch(output, bridge=bridge)
        assert result["episodes"] == 2
        assert result["labeled_pairs"] == 12
        assert result["queries"] == 8
        private = output / "private" / f"{index['public_ids'][0]}.json"
        original = private.read_bytes()
        value = json.loads(original)
        value["test"][0]["output"][0][0] = False
        private.write_text(json.dumps(value))
        with pytest.raises(ValueError, match="integer"):
            prototype.verify_batch(output, bridge=bridge)
        private.write_bytes(original)
        value = json.loads(original)
        value["racket"] = {"backend": "python", "protected": False}
        private.write_text(json.dumps(value))
        with pytest.raises(ValueError, match="runtime"):
            prototype.verify_batch(output, bridge=bridge)


def test_duplicate_export_refusal_is_atomic(tmp_path):
    prototype = load_prototype()
    episode = prototype.sample_episode(7, marker_color=8, n_demo=2, n_query=1)
    output = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="duplicate"):
        prototype.write_batch([episode, episode], output)
    assert not output.exists()
