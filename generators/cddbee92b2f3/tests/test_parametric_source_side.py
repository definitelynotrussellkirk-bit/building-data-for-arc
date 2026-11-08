from __future__ import annotations

import copy
import importlib.util
import json
import random

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "cddbee92b2f3"
ROOT = find_root(__file__)
HERE = ROOT / f"generators/{TASK_ID}/workspace/parametric"


def load_module(filename: str = "prototype.py"):
    path = HERE / filename
    assert path.is_file(), f"source-side prototype is not implemented: {path}"
    spec = importlib.util.spec_from_file_location(f"cdd_source_side_{filename}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical task missing")


def test_default_program_is_exact_canonical_and_directional_copy_is_hand_derived():
    p = load_module()
    assert p.program({"source_side": "left"}) == canonical_program()
    assert p.program({"source_side": "right"}) != canonical_program()

    grid = [[0] * 9 for _ in range(5)]
    for row in range(5):
        grid[row][4] = 5
    grid[1][2] = 2
    grid[1][6] = 7
    grid[2][3] = 3
    grid[2][5] = 8
    grid[4][8] = 9

    left = p.transform(grid, {"source_side": "left"})
    right = p.transform(grid, {"source_side": "right"})
    assert left[1][6] == 2 and left[1][2] == 2
    assert left[2][5] == 3 and left[4][8] == 9
    assert right[1][2] == 7 and right[1][6] == 7
    assert right[2][3] == 8 and right[4][8] == 9  # off-canvas mirror is clipped
    assert grid[1][2] == 2 and grid[1][6] == 7


def test_first_guide_overwrite_filter_and_clipping_are_preserved_in_both_directions():
    p = load_module()
    grid = [[0] * 11 for _ in range(6)]
    for row in range(6):
        grid[row][3] = 5
        grid[row][8] = 5
    grid[1][1] = 2   # first-guide left source -> col 5
    grid[1][5] = 9   # occupied target / right source -> col 1
    grid[2][2] = 5   # literal five is not a source
    grid[3][10] = 7  # right source clips past col 0 under first guide

    left = p.transform(grid, {"source_side": "left"})
    right = p.transform(grid, {"source_side": "right"})
    assert left[1][5] == 2
    assert left[2][4] == 0
    assert right[1][1] == 9
    assert right[3][10] == 7
    assert all(left[row][3] == 5 and right[row][3] == 5 for row in range(6))
    assert all(left[row][8] == 5 and right[row][8] == 5 for row in range(6))


def test_strict_settings_counts_and_malformed_inputs_fail_closed():
    p = load_module()
    for settings in ({}, {"source_side": "both"}, {"source_side": True}, {"source_side": "left", "extra": 0}):
        with pytest.raises(ValueError):
            p.program(settings)
    for kwargs in (
        {"seed": True, "settings": p.DEFAULT, "demos": 3, "queries": 4},
        {"seed": 1, "settings": p.DEFAULT, "demos": 1, "queries": 4},
        {"seed": 1, "settings": p.DEFAULT, "demos": 7, "queries": 4},
        {"seed": 1, "settings": p.DEFAULT, "demos": 3, "queries": 3},
        {"seed": 1, "settings": p.DEFAULT, "demos": 3, "queries": 5},
    ):
        with pytest.raises(ValueError):
            p.generate(**kwargs)
    for grid in ([], [[]], [[True]], [[0], [0, 1]], [[10]]):
        with pytest.raises(ValueError):
            p.transform(grid, p.DEFAULT)


def test_setting_neutral_generation_has_distinct_four_query_30x30_stress():
    p = load_module()
    random.seed(441)
    state = random.getstate()
    left = p.generate(29, {"source_side": "left"}, demos=2, queries=4)
    assert random.getstate() == state
    assert left == p.generate(29, {"source_side": "left"}, demos=2, queries=4)
    right = p.generate(29, {"source_side": "right"}, demos=2, queries=4)
    assert [pair["input"] for pair in left["train"] + left["test"]] == [
        pair["input"] for pair in right["train"] + right["test"]
    ]
    assert [pair["output"] for pair in left["train"]] != [pair["output"] for pair in right["train"]]
    assert left["certificate"]["survivors"] == [{"source_side": "left"}]
    assert right["certificate"]["survivors"] == [{"source_side": "right"}]
    assert [(len(pair["input"]), len(pair["input"][0])) for pair in left["test"]] == [
        (12, 15), (16, 20), (24, 27), (30, 30)
    ]
    assert len({json.dumps(pair["input"], separators=(",", ":")) for pair in left["train"] + left["test"]}) == 6

    maximum = p.generate(101, {"source_side": "right"}, demos=6, queries=4)
    assert len(maximum["train"]) == 6 and len(maximum["test"]) == 4
    assert maximum["certificate"]["survivors"] == [{"source_side": "right"}]


def test_public_projection_is_private_invariant_and_has_no_future_answers():
    p = load_module()
    episode = p.generate(13, p.DEFAULT, demos=3, queries=4)
    body = public_challenge_bytes(episode)
    visible = json.loads(body)
    assert all(set(pair) == {"input"} for pair in visible["test"])
    assert visible["test"][0]["input"] == episode["test"][0]["input"]

    changed = copy.deepcopy(episode)
    changed["settings"] = {"private": "changed"}
    changed["program_solution"] = "changed"
    changed["test"][3]["output"] = [[9]]
    assert public_challenge_bytes(changed) == body
    assert public_challenge_id(changed) == public_challenge_id(episode)


def test_racket_executes_both_settings_and_all_labels():
    p = load_module()
    with p.RacketRunner() as execute:
        for setting in p.SETTINGS:
            episode = p.generate(47, setting, demos=2, queries=4)
            certificate = p.certify(episode, execute)
            assert certificate["racket_checked"] is True
            assert certificate["survivors"] == [setting]
            assert len(certificate["queries"]) == 4


def test_adapter_supports_six_demos_and_rejects_nonfour_queries():
    p = load_module()
    adapter = load_module("adapter.py")
    episode = adapter.generate(5, p.DEFAULT, 6, 4)
    assert len(episode["train"]) == 6 and len(episode["test"]) == 4
    assert episode["program_solution"] == canonical_program()
    with pytest.raises(ValueError):
        adapter.generate(5, p.DEFAULT, 6, 3)


def test_sequential_reveal_exposes_one_query_without_future_hints(tmp_path):
    p = load_module()
    episode = p.generate(73, p.DEFAULT, demos=3, queries=4)
    first = p.public_turn_bytes(episode, 0)
    visible = json.loads(first)
    assert set(visible) == {"train", "test"}
    assert len(visible["test"]) == 1
    assert visible["test"][0] == {"input": episode["test"][0]["input"]}
    assert first == public_challenge_bytes({"train": episode["train"], "test": episode["test"][:1]})

    changed = copy.deepcopy(episode)
    changed["settings"] = {"private": "changed"}
    changed["program_solution"] = "changed"
    changed["test"][0]["output"] = [[9]]
    changed["test"][3]["input"] = [[9]]
    assert p.public_turn_bytes(changed, 0) == first
    with pytest.raises(ValueError):
        p.public_turn_bytes(episode, -1)
    with pytest.raises(ValueError):
        p.public_turn_bytes(episode, 4)

    exported = tmp_path / "export"
    manifest = p.write_batch([episode], exported)
    assert len(manifest["public_ids"]) == 4
    assert len(manifest["episodes"][0]["turn_ids"]) == 4
    assert manifest["public_usage"].startswith("Serve only the next")
    assert manifest["controller_usage"].endswith("not a model prompt.")
    assert manifest["manifest_usage"].startswith("Controller metadata")
    assert all(len(json.loads(path.read_text())["test"]) == 1 for path in (exported / "public").iterdir())
    controller = exported / manifest["episodes"][0]["controller"]
    assert len(json.loads(controller.read_text())["test"]) == 4
