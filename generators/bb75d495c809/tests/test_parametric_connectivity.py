from __future__ import annotations

import copy
import importlib.util
import json
import random

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "bb75d495c809"
ROOT = find_root(__file__)
HERE = ROOT / f"generators/{TASK_ID}/workspace/parametric"


def load_module(filename: str = "prototype.py"):
    path = HERE / filename
    assert path.is_file(), f"connectivity prototype is not implemented: {path}"
    spec = importlib.util.spec_from_file_location(f"bb75_connectivity_{filename}", path)
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


def test_default_program_is_exact_canonical_and_diagonal_pair_is_hand_derived():
    p = load_module()
    assert p.program({"connectivity": 4}) == canonical_program()
    assert p.program({"connectivity": 8}) != canonical_program()

    grid = [[5] * 8 for _ in range(7)]
    grid[1][1] = 0
    grid[2][2] = 0  # diagonal-only contact
    grid[1][5] = grid[1][6] = 0  # standalone domino
    grid[4][4] = grid[5][4] = grid[5][5] = 0  # standalone triomino

    four = p.transform(grid, {"connectivity": 4})
    eight = p.transform(grid, {"connectivity": 8})
    assert four[1][1] == four[2][2] == 3
    assert eight[1][1] == eight[2][2] == 2
    assert four[1][5] == four[1][6] == 2
    assert four[4][4] == four[5][4] == four[5][5] == 1
    assert grid[1][1] == 0


def test_size_four_or_more_stays_zero_under_selected_connectivity():
    p = load_module()
    grid = [[6] * 7 for _ in range(7)]
    for r, c in ((2, 2), (2, 3), (3, 2), (3, 3)):
        grid[r][c] = 0
    for setting in p.SETTINGS:
        output = p.transform(grid, setting)
        assert all(output[r][c] == 0 for r, c in ((2, 2), (2, 3), (3, 2), (3, 3)))


def test_strict_settings_counts_and_malformed_inputs_fail_closed():
    p = load_module()
    for settings in ({}, {"connectivity": 6}, {"connectivity": True}, {"connectivity": 4, "extra": 0}):
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
    for grid in ([], [[]], [[True]], [[5], [5, 5]], [[10]]):
        with pytest.raises(ValueError):
            p.transform(grid, p.DEFAULT)


def test_setting_neutral_generation_has_distinct_four_query_30x30_stress():
    p = load_module()
    random.seed(991)
    state = random.getstate()
    four = p.generate(31, {"connectivity": 4}, demos=2, queries=4)
    assert random.getstate() == state
    assert four == p.generate(31, {"connectivity": 4}, demos=2, queries=4)
    eight = p.generate(31, {"connectivity": 8}, demos=2, queries=4)
    assert [pair["input"] for pair in four["train"] + four["test"]] == [
        pair["input"] for pair in eight["train"] + eight["test"]
    ]
    assert [pair["output"] for pair in four["train"]] != [pair["output"] for pair in eight["train"]]
    assert four["certificate"]["survivors"] == [{"connectivity": 4}]
    assert eight["certificate"]["survivors"] == [{"connectivity": 8}]
    assert [(len(pair["input"]), len(pair["input"][0])) for pair in four["test"]] == [
        (10, 10), (16, 18), (24, 26), (30, 30)
    ]
    assert len({json.dumps(pair["input"], separators=(",", ":")) for pair in four["train"] + four["test"]}) == 6

    maximum = p.generate(103, {"connectivity": 8}, demos=6, queries=4)
    assert len(maximum["train"]) == 6 and len(maximum["test"]) == 4
    assert maximum["certificate"]["survivors"] == [{"connectivity": 8}]


def test_public_projection_is_private_invariant_and_has_no_future_answers():
    p = load_module()
    episode = p.generate(17, p.DEFAULT, demos=3, queries=4)
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
            episode = p.generate(53, setting, demos=2, queries=4)
            certificate = p.certify(episode, execute)
            assert certificate["racket_checked"] is True
            assert certificate["survivors"] == [setting]
            assert len(certificate["queries"]) == 4


def test_adapter_supports_six_demos_and_rejects_nonfour_queries():
    p = load_module()
    adapter = load_module("adapter.py")
    episode = adapter.generate(7, p.DEFAULT, 6, 4)
    assert len(episode["train"]) == 6 and len(episode["test"]) == 4
    assert episode["program_solution"] == canonical_program()
    with pytest.raises(ValueError):
        adapter.generate(7, p.DEFAULT, 6, 3)


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
