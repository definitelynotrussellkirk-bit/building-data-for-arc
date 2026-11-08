from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "d07a6cba78c7"
ROOT = find_root(__file__)
HERE = ROOT / f"generators/{TASK_ID}/workspace/parametric"
PROTOTYPE = HERE / "prototype.py"


def load_module(filename: str = "prototype.py"):
    path = HERE / filename
    assert path.is_file(), f"marker-side prototype is not implemented: {path}"
    spec = importlib.util.spec_from_file_location(f"d07_marker_side_{filename}", path)
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


def test_default_program_is_exact_canonical_and_right_rule_changes_behavior():
    p = load_module()
    assert p.program({"marker_side": "left"}) == canonical_program()
    assert p.program({"marker_side": "right"}) != canonical_program()

    grid = [
        [0, 1, 0, 0, 0],
        [6, 2, 3, 0, 0],
        [0, 4, 0, 5, 6],
        [0, 7, 8, 0, 0],
    ]
    assert p.transform(grid, {"marker_side": "left"}) == [[2, 3, 0, 0]]
    assert p.transform(grid, {"marker_side": "right"}) == [[0, 4, 0, 5]]
    assert p._first_row_rival(grid, {"marker_side": "left"}) == [grid[0][1:]]
    assert p._first_row_rival(grid, {"marker_side": "right"}) == [grid[0][:-1]]
    assert grid[1][0] == 6 and grid[2][-1] == 6


def test_strict_settings_counts_and_malformed_grids_fail_closed():
    p = load_module()
    for settings in ({}, {"marker_side": "top"}, {"marker_side": True}, {"marker_side": "left", "extra": 1}):
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
    for grid in ([], [[]], [[True]], [[0], [0, 1]], [[10]], [[0, 1], [0, 2]]):
        with pytest.raises(ValueError):
            p.transform(grid, p.DEFAULT)


def test_generation_is_setting_neutral_deterministic_and_four_query_stress_is_distinct():
    p = load_module()
    random.seed(991)
    state = random.getstate()
    left = p.generate(17, {"marker_side": "left"}, demos=2, queries=4)
    assert random.getstate() == state
    assert left == p.generate(17, {"marker_side": "left"}, demos=2, queries=4)
    right = p.generate(17, {"marker_side": "right"}, demos=2, queries=4)
    assert [pair["input"] for pair in left["train"] + left["test"]] == [
        pair["input"] for pair in right["train"] + right["test"]
    ]
    assert [pair["output"] for pair in left["train"]] != [pair["output"] for pair in right["train"]]
    assert left["certificate"]["survivors"] == [{"marker_side": "left"}]
    assert right["certificate"]["survivors"] == [{"marker_side": "right"}]
    assert len(left["train"]) == 2 and len(left["test"]) == 4
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in left["test"]]
    assert shapes == [(9, 11), (13, 17), (20, 24), (30, 30)]
    all_inputs = left["train"] + left["test"]
    assert len({json.dumps(pair["input"], separators=(",", ":")) for pair in all_inputs}) == 6

    maximum = p.generate(99, {"marker_side": "right"}, demos=6, queries=4)
    assert len(maximum["train"]) == 6 and len(maximum["test"]) == 4
    assert maximum["certificate"]["survivors"] == [{"marker_side": "right"}]


def test_public_projection_hides_private_fields_and_query_answers():
    p = load_module()
    episode = p.generate(31, p.DEFAULT, demos=3, queries=4)
    original = public_challenge_bytes(episode)
    visible = json.loads(original)
    assert set(visible) == {"train", "test"}
    assert all(set(pair) == {"input"} for pair in visible["test"])
    assert visible["test"][0]["input"] == episode["test"][0]["input"]

    changed = copy.deepcopy(episode)
    changed["settings"] = {"private": "changed"}
    changed["program_solution"] = "private program changed"
    changed["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(changed) == original
    assert public_challenge_id(changed) == public_challenge_id(episode)


def test_racket_executes_both_settings_and_all_retained_labels():
    p = load_module()
    with p.RacketRunner() as execute:
        for setting in p.SETTINGS:
            episode = p.generate(43, setting, demos=2, queries=4)
            certificate = p.certify(episode, execute)
            assert certificate["racket_checked"] is True
            assert certificate["survivors"] == [setting]
            assert len(certificate["queries"]) == 4


def test_thin_adapter_supports_maximum_demo_count_and_exact_four_queries():
    p = load_module()
    adapter = load_module("adapter.py")
    episode = adapter.generate(7, p.DEFAULT, 6, 4)
    assert len(episode["train"]) == 6
    assert len(episode["test"]) == 4
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
