from __future__ import annotations

import importlib.util
import json

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "aea4d55345a1"
ROOT = find_root(__file__)
MODULE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"


def load_prototype():
    assert MODULE_PATH.is_file(), "parametric prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("sequence_carry_test_subject", MODULE_PATH)
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
    assert prototype.program({"carry_policy": "skipped_rows"}) == canonical_program()


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"carry_policy": "all_rows"}, {"carry_policy": 1},
     {"carry_policy": "skipped_rows", "extra": 1}],
)
def test_program_rejects_invalid_settings(settings):
    prototype = load_prototype()
    with pytest.raises(ValueError):
        prototype.program(settings)

import copy

from reviewer_support import public_challenge_bytes, public_challenge_id


def grid_key(grid):
    return tuple(tuple(row) for row in grid)


def split_sections(grid):
    separators = [
        r for r, row in enumerate(grid)
        if row and all(value == 5 for value in row)
    ]
    assert len(separators) == 3
    section_height = separators[0]
    starts = [0] + [r + 1 for r in separators]
    return [
        [row[:] for row in grid[start : start + section_height]]
        for start in starts
    ]


def assemble(sections):
    width = len(sections[0][0])
    grid = []
    for index, section in enumerate(sections):
        grid.extend(copy.deepcopy(section))
        if index < len(sections) - 1:
            grid.append([5] * width)
    return grid


def ambiguous_latest_grid(width, anchor, signature):
    sections = [[[0 for _ in range(width)] for _ in range(2)] for _ in range(4)]
    cells = range(anchor - 2, anchor + 4)
    for step, section in enumerate(sections):
        for col in cells:
            section[0][col] = 1
        for col in range(anchor - 2, anchor - 1 + step):
            section[0][col] = 2
        section[1][signature] = 3
    return assemble(sections)


def test_carry_policies_differ_on_all_query_shapes():
    prototype = load_prototype()
    for offset in range(4):
        grid = prototype.sample_input(17, 100 + offset)
        before = copy.deepcopy(grid)
        carried = prototype.transform(grid, carry_policy="skipped_rows")
        latest = prototype.transform(grid, carry_policy="latest_only")
        assert carried != latest
        assert grid == before
        sections = split_sections(grid)
        assert (len(carried), len(carried[0])) == (len(sections[0]), len(grid[0]))


@pytest.mark.parametrize("n_demo", range(2, 7))
@pytest.mark.parametrize("policy", ["skipped_rows", "latest_only"])
def test_counts_unique_queries_and_demo_only_teaching(n_demo, policy):
    prototype = load_prototype()
    episode = prototype.sample_episode(23, carry_policy=policy, n_demo=n_demo, n_query=4)
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
    a = prototype.sample_episode(83, carry_policy="skipped_rows", n_demo=3, n_query=4)
    b = prototype.sample_episode(83, carry_policy="latest_only", n_demo=3, n_query=4)
    for split in ("train", "test"):
        assert [pair["input"] for pair in a[split]] == [pair["input"] for pair in b[split]]
    one = prototype.sample_episode(83, carry_policy="skipped_rows", n_demo=3, n_query=1)
    assert a["test"][:1] == one["test"]
    assert prototype.first_turn(a) == prototype.first_turn(one)
    six = prototype.sample_episode(83, carry_policy="skipped_rows", n_demo=6, n_query=4)
    assert a["train"] == six["train"][:3]
    assert a["test"] == six["test"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True}, {"seed": -1},
        {"n_demo": 1}, {"n_demo": 7}, {"n_demo": True}, {"n_demo": 3.0},
        {"n_query": 0}, {"n_query": 5}, {"n_query": False}, {"n_query": 4.0},
        {"carry_policy": "all_rows"}, {"carry_policy": True},
    ],
)
def test_invalid_episode_requests_reject(kwargs):
    prototype = load_prototype()
    request = {"seed": 0, "carry_policy": "skipped_rows", "n_demo": 3, "n_query": 4}
    request.update(kwargs)
    with pytest.raises(ValueError):
        prototype.sample_episode(**request)


def test_four_queries_cover_structural_shapes_and_27x30_stress():
    prototype = load_prototype()
    episode = prototype.sample_episode(101, carry_policy="skipped_rows", n_demo=2, n_query=4)
    queries = [pair["input"] for pair in episode["test"]]
    assert [(len(grid), len(grid[0])) for grid in queries] == [
        (15, 11), (19, 16), (23, 22), (27, 30)
    ]
    assert [(len(pair["output"]), len(pair["output"][0])) for pair in episode["test"]] == [
        (3, 11), (4, 16), (5, 22), (6, 30)
    ]
    largest = queries[-1]
    carried = prototype.transform(largest, carry_policy="skipped_rows")
    latest = prototype.transform(largest, carry_policy="latest_only")
    assert sum(a != b for ra, rb in zip(carried, latest) for a, b in zip(ra, rb)) >= 4
    assert sum(value not in (0, 5) for row in largest for value in row) >= 100
    assert len([row for row in largest if all(value == 5 for value in row)]) == 3


def test_public_identity_and_first_turn_use_visible_bytes_only():
    prototype = load_prototype()
    episode = prototype.sample_episode(91, carry_policy="skipped_rows", n_demo=2, n_query=4)
    changed = copy.deepcopy(episode)
    changed.update(seed=999, parameters={"carry_policy": "latest_only"}, program="secret")
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
    for width, anchor, signature in ((11, 4, 9), (12, 5, 10)):
        grid = ambiguous_latest_grid(width, anchor, signature)
        demos.append({
            "input": grid,
            "output": prototype.transform(grid, carry_policy="skipped_rows"),
        })
    query = prototype.sample_input(9, 101)
    episode = {
        "train": demos,
        "test": [{
            "input": query,
            "output": prototype.transform(query, carry_policy="skipped_rows"),
        }],
    }
    certificate = prototype.lesson_certificate(episode)
    assert certificate["survivors"] == ["skipped_rows", "latest_only"]
    assert certificate["identifiable"] is False
    assert certificate["query_agreement"] == [False]


def test_racket_labels_export_replay_and_tamper_rejection(tmp_path):
    prototype = load_prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(timeout=15) as bridge:
        episodes = [
            prototype.generate_episode(17, carry_policy=policy, n_demo=2, n_query=4, bridge=bridge)
            for policy in ("skipped_rows", "latest_only")
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
    episode = prototype.sample_episode(7, carry_policy="skipped_rows", n_demo=2, n_query=1)
    output = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="duplicate"):
        prototype.write_batch([episode, episode], output)
    assert not output.exists()
