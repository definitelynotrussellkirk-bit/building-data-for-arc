"""Native contract tests for cue-directed symbolic expansion."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break

from reviewer_support import canonical_path, find_root  # noqa: E402

TASK_ID = "7d1e8744229a"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name: str, path: Path):
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical row missing")


def test_native_files_exist_and_default_program_is_exact():
    proto = _load("arc_7d_proto", HOME / "prototype.py")
    adapter = _load("arc_7d_adapter", HOME / "adapter.py")
    promotion = json.loads((HOME / "promotion.json").read_text())

    assert proto.MODES == ("canonical", "cue_rotate_erase")
    assert proto.CUE_POSITIONS == ((0, 2), (2, 4), (4, 2), (2, 0))
    assert adapter.program({"mode": "canonical"}) == _canonical_program()
    assert proto.program_for("canonical") == _canonical_program()
    assert promotion["default"] == {"mode": "canonical"}
    assert promotion["limits"] == {"demos": [4, 6], "queries": [1, 4]}
    assert promotion["qualification_demos"] == 4


def test_episode_counts_matched_inputs_and_four_query_bank():
    adapter = _load("arc_7d_adapter_counts", HOME / "adapter.py")
    canonical = adapter.generate(17, {"mode": "canonical"}, demos=4, queries=4)
    sequential = adapter.generate(17, {"mode": "cue_rotate_erase"}, demos=4, queries=4)

    assert len(canonical["train"]) == len(sequential["train"]) == 4
    assert len(canonical["test"]) == len(sequential["test"]) == 4
    assert [p["input"] for p in canonical["train"] + canonical["test"]] == [
        p["input"] for p in sequential["train"] + sequential["test"]
    ]
    inputs = [json.dumps(p["input"], separators=(",", ":")) for p in canonical["train"] + canonical["test"]]
    assert len(inputs) == len(set(inputs)) == 8
    assert {tuple(proto_pos) for proto_pos in (
        next((r, c) for r, row in enumerate(pair["input"]) for c, value in enumerate(row) if value == 0)
        for pair in canonical["train"]
    )} == {(0, 2), (2, 4), (4, 2), (2, 0)}


def test_python_labels_are_exact_and_sequential_stage_is_substantive():
    proto = _load("arc_7d_proto_labels", HOME / "prototype.py")
    for mode in proto.MODES:
        episode = proto.generate_episode(23, mode, demos=4, queries=4)
        for pair in episode["train"] + episode["test"]:
            before = deepcopy(pair["input"])
            assert pair["output"] == proto.solve(pair["input"], mode)
            assert pair["input"] == before
            assert len(pair["output"]) == len(pair["output"][0]) == 10
            if mode == "cue_rotate_erase":
                intermediate = proto.rotated_intermediate(pair["input"])
                changed = sum(
                    intermediate[r][c] != pair["output"][r][c]
                    for r in range(10)
                    for c in range(10)
                )
                assert 13 <= changed <= 19
                assert all(
                    pair["output"][r][c] == 0
                    for r, c in proto.north_component(intermediate)
                )


def test_four_demos_refute_named_rivals_and_the_other_setting():
    proto = _load("arc_7d_proto_teaching", HOME / "prototype.py")
    for mode in proto.MODES:
        episode = proto.generate_episode(31, mode, demos=4, queries=4)
        certificate = proto.teaching_certificate(episode, mode)
        assert certificate["surviving_rivals"] == []
        assert certificate["query_changing_survivors"] == []
        assert certificate["rivals_checked"] >= 5


def test_public_turn_is_single_query_and_first_turn_prefix_stable():
    adapter = _load("arc_7d_adapter_public", HOME / "adapter.py")
    four = adapter.generate(99, {"mode": "cue_rotate_erase"}, demos=4, queries=4)
    one = adapter.generate(99, {"mode": "cue_rotate_erase"}, demos=4, queries=1)
    first = adapter.public_turn(four, 0)
    assert first == adapter.public_turn(one, 0)
    assert set(first) == {"train", "test"}
    assert len(first["test"]) == 1
    assert "output" not in first["test"][0]
    for index in range(1, 4):
        turn = adapter.public_turn(four, index)
        assert set(turn) == {"test"}
        assert turn == {"test": [{"input": four["test"][index]["input"]}]}


def test_strict_settings_counts_and_cue_grammar_reject_bad_inputs():
    proto = _load("arc_7d_proto_validation", HOME / "prototype.py")
    adapter = _load("arc_7d_adapter_validation", HOME / "adapter.py")
    for bad in ({}, {"mode": "bad"}, {"mode": "canonical", "extra": 1}, None):
        with pytest.raises((TypeError, ValueError)):
            adapter.program(bad)
    for demos in (3, 7, True):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, {"mode": "canonical"}, demos=demos, queries=4)
    episode = proto.generate_episode(0, "cue_rotate_erase", demos=4, queries=4)
    bad = deepcopy(episode["train"][0]["input"])
    bad[1][1] = 0
    with pytest.raises(ValueError):
        proto.solve(bad, "cue_rotate_erase")
