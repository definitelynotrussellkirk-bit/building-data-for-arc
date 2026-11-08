from __future__ import annotations

import importlib.util
import json

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "46c02325ed3b"
ROOT = find_root(__file__)
MODULE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"


def load_prototype():
    assert MODULE_PATH.is_file(), "parametric prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("waterfall_spread_test_subject", MODULE_PATH)
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
    assert prototype.program({"spread_policy": "both"}) == canonical_program()


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"spread_policy": "left_only"}, {"spread_policy": 1},
     {"spread_policy": "both", "extra": 1}],
)
def test_program_rejects_invalid_settings(settings):
    prototype = load_prototype()
    with pytest.raises(ValueError):
        prototype.program(settings)

import copy

from reviewer_support import public_challenge_bytes, public_challenge_id


def grid_key(grid):
    return tuple(tuple(row) for row in grid)


def source_edge(grid):
    h, w = len(grid), len(grid[0])
    sources = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    assert len(sources) == 1
    r, c = sources[0]
    memberships = [
        name
        for name, condition in (
            ("top", r == 0), ("bottom", r == h - 1),
            ("left", c == 0), ("right", c == w - 1),
        )
        if condition
    ]
    assert len(memberships) == 1
    return memberships[0]


def wall_count(grid):
    edge = source_edge(grid)
    if edge in ("top", "bottom"):
        return sum(any(value == 8 for value in row) for row in grid)
    return sum(any(grid[r][c] == 8 for r in range(len(grid))) for c in range(len(grid[0])))


def ambiguous_no_wall_input(source_col):
    grid = [[0] * 10 for _ in range(10)]
    grid[0][source_col] = 2
    return grid


def test_spread_policies_differ_on_all_four_source_edges():
    prototype = load_prototype()
    expected_edges = ["top", "bottom", "left", "right"]
    for offset, expected_edge in enumerate(expected_edges):
        grid = prototype.sample_input(17, 100 + offset)
        before = copy.deepcopy(grid)
        output_both = prototype.transform(grid, spread_policy="both")
        output_right = prototype.transform(grid, spread_policy="right_hand_only")
        assert output_both != output_right
        assert grid == before
        assert source_edge(grid) == expected_edge
        assert len(output_both) == len(grid)
        assert all(len(row) == len(grid[0]) for row in output_both)


@pytest.mark.parametrize("n_demo", range(2, 7))
@pytest.mark.parametrize("policy", ["both", "right_hand_only"])
def test_counts_unique_queries_and_demo_only_teaching(n_demo, policy):
    prototype = load_prototype()
    episode = prototype.sample_episode(23, spread_policy=policy, n_demo=n_demo, n_query=4)
    assert len(episode["train"]) == n_demo
    assert len(episode["test"]) == 4
    pairs = episode["train"] + episode["test"]
    assert len({grid_key(pair["input"]) for pair in pairs}) == len(pairs)
    certificate = prototype.lesson_certificate(episode)
    assert certificate["survivors"] == [policy]
    assert certificate["identifiable"] is True
    changed = copy.deepcopy(episode)
    for pair in changed["test"]:
        pair["output"] = [[False]]
    assert prototype.lesson_certificate(changed) == certificate


def test_matched_settings_query_prefix_and_demo_count_independence():
    prototype = load_prototype()
    a = prototype.sample_episode(83, spread_policy="both", n_demo=3, n_query=4)
    b = prototype.sample_episode(83, spread_policy="right_hand_only", n_demo=3, n_query=4)
    for split in ("train", "test"):
        assert [pair["input"] for pair in a[split]] == [pair["input"] for pair in b[split]]
    one = prototype.sample_episode(83, spread_policy="both", n_demo=3, n_query=1)
    assert a["test"][:1] == one["test"]
    assert prototype.first_turn(a) == prototype.first_turn(one)
    six = prototype.sample_episode(83, spread_policy="both", n_demo=6, n_query=4)
    assert a["train"] == six["train"][:3]
    assert a["test"] == six["test"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True}, {"seed": -1},
        {"n_demo": 1}, {"n_demo": 7}, {"n_demo": True}, {"n_demo": 3.0},
        {"n_query": 0}, {"n_query": 5}, {"n_query": False}, {"n_query": 4.0},
        {"spread_policy": "left_only"}, {"spread_policy": True},
    ],
)
def test_invalid_episode_requests_reject(kwargs):
    prototype = load_prototype()
    request = {"seed": 0, "spread_policy": "both", "n_demo": 3, "n_query": 4}
    request.update(kwargs)
    with pytest.raises(ValueError):
        prototype.sample_episode(**request)


def test_four_queries_cover_rotations_and_substantive_30x30_stress():
    prototype = load_prototype()
    episode = prototype.sample_episode(101, spread_policy="both", n_demo=2, n_query=4)
    queries = [pair["input"] for pair in episode["test"]]
    assert [(len(grid), len(grid[0])) for grid in queries] == [
        (10, 10), (14, 17), (18, 18), (30, 30)
    ]
    assert [source_edge(grid) for grid in queries] == ["top", "bottom", "left", "right"]
    assert [wall_count(grid) for grid in queries] == [2, 3, 4, 5]
    largest = queries[-1]
    both = prototype.transform(largest, spread_policy="both")
    right = prototype.transform(largest, spread_policy="right_hand_only")
    assert sum(a != b for ra, rb in zip(both, right) for a, b in zip(ra, rb)) >= 20
    assert sum(value == 8 for row in largest for value in row) >= 100


def test_public_identity_and_first_turn_use_visible_bytes_only():
    prototype = load_prototype()
    episode = prototype.sample_episode(91, spread_policy="both", n_demo=2, n_query=4)
    changed = copy.deepcopy(episode)
    changed.update(seed=999, parameters={"spread_policy": "right_hand_only"}, program="secret")
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
    demos = []
    for source_col in (4, 5):
        grid = ambiguous_no_wall_input(source_col)
        demos.append({"input": grid, "output": prototype.transform(grid, spread_policy="both")})
    query = prototype.sample_input(9, 101)
    episode = {
        "train": demos,
        "test": [{"input": query, "output": prototype.transform(query, spread_policy="both")}],
    }
    certificate = prototype.lesson_certificate(episode)
    assert certificate["survivors"] == ["both", "right_hand_only"]
    assert certificate["identifiable"] is False
    assert certificate["query_agreement"] == [False]


def test_racket_labels_export_replay_and_tamper_rejection(tmp_path):
    prototype = load_prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(timeout=15) as bridge:
        episodes = [
            prototype.generate_episode(17, spread_policy=policy, n_demo=2, n_query=4, bridge=bridge)
            for policy in ("both", "right_hand_only")
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
    episode = prototype.sample_episode(7, spread_policy="both", n_demo=2, n_query=1)
    output = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="duplicate"):
        prototype.write_batch([episode, episode], output)
    assert not output.exists()
