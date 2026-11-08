from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "8c73e339d80e"
ROOT = find_root(__file__)
SOURCE = ROOT / f"generators/{TASK_ID}/workspace/parametric/prototype.py"


def _load():
    assert SOURCE.is_file(), "task-local handedness prototype is missing"
    spec = importlib.util.spec_from_file_location("parametric_8c73_handedness", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def proto():
    return _load()


def _canonical_program():
    ledger = ROOT / "shared/data/canonical/puzzles.jsonl"
    for line in ledger.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError(TASK_ID)


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_program_is_exact_canonical_and_alternate_only_changes_handedness(proto):
    canonical = _canonical_program()
    assert proto.program({"direction": "clockwise"}) == canonical
    alternate = proto.program({"direction": "counterclockwise"})
    assert alternate != canonical
    assert "[(= v 4) 3]" in alternate
    assert "[(= v 9) 1]" in alternate


def test_counts_fixed_setting_matched_inputs_and_30x30_stress(proto):
    cw = proto.generate(17, {"direction": "clockwise"}, demos=3, queries=4)
    ccw = proto.generate(17, {"direction": "counterclockwise"}, demos=3, queries=4)
    assert cw["settings"] == {"direction": "clockwise"}
    assert ccw["settings"] == {"direction": "counterclockwise"}
    assert len(cw["train"]) == len(ccw["train"]) == 3
    assert len(cw["test"]) == len(ccw["test"]) == 4
    assert _inputs(cw) == _inputs(ccw)
    assert len({proto.digest(grid) for grid in _inputs(cw)}) == 7
    assert (len(cw["test"][-1]["input"]), len(cw["test"][-1]["input"][0])) == (30, 30)
    occupied = [(r, c) for r, row in enumerate(cw["test"][-1]["input"]) for c, v in enumerate(row) if v]
    assert max(r for r, _ in occupied) - min(r for r, _ in occupied) >= 25
    assert max(c for _, c in occupied) - min(c for _, c in occupied) >= 25
    assert {5, 7} <= {value for row in cw["test"][-1]["input"] for value in row}
    assert any(a["output"] != b["output"] for a, b in zip(cw["train"], ccw["train"]))
    assert cw["certificate"]["survivors"] == [{"direction": "clockwise"}]
    assert ccw["certificate"]["survivors"] == [{"direction": "counterclockwise"}]


@pytest.mark.parametrize("demos", [2, 6])
def test_supported_demo_boundaries_keep_four_queries(proto, demos):
    episode = proto.generate(3, {"direction": "clockwise"}, demos=demos, queries=4)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    assert episode["certificate"]["survivors"] == [{"direction": "clockwise"}]


def test_real_racket_labels_both_settings_and_demo_only_identification(proto):
    with RacketBridge() as bridge:
        for direction in ("clockwise", "counterclockwise"):
            episode = proto.generate(29, {"direction": direction}, demos=3, queries=4)
            for pair in episode["train"] + episode["test"]:
                assert proto.execute_rule(episode["program_solution"], pair["input"], bridge=bridge) == pair["output"]
            cert = proto.certify(episode, execute=lambda source, grid: proto.execute_rule(source, grid, bridge=bridge))
            assert cert["survivors"] == [{"direction": direction}]
            assert all(row["unanimous"] for row in cert["queries"])


def test_public_projection_ignores_private_answers_and_settings(proto):
    episode = proto.generate(41, {"direction": "clockwise"}, demos=3, queries=4)
    before = public_challenge_bytes(episode)
    assert proto.public_challenge(episode) == json.loads(before)
    assert proto.public_id(episode) == public_challenge_id(episode)
    changed = copy.deepcopy(episode)
    changed["settings"] = {"direction": "counterclockwise"}
    changed["program_solution"] = "private mutation"
    changed["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(changed) == before
    assert proto.public_id(changed) == proto.public_id(episode)


def test_query_prefix_is_independent_of_demo_count(proto):
    single = proto.generate(13, {"direction": "clockwise"}, demos=2, queries=1)
    multi = proto.generate(13, {"direction": "clockwise"}, demos=6, queries=4)
    assert single["test"] == multi["test"][:1]
    assert proto.public_challenge(single)["test"][0] == proto.public_challenge(multi)["test"][0]


def test_invalid_contracts_and_corrupt_label_fail_closed(proto):
    for overrides in ({"demos": 1}, {"demos": 7}, {"queries": 0}):
        request = {"demos": 3, "queries": 4}
        request.update(overrides)
        with pytest.raises(ValueError):
            proto.generate(0, {"direction": "clockwise"}, **request)
    with pytest.raises(ValueError):
        proto.generate(0, {"direction": "sideways"}, demos=3, queries=4)
    episode = proto.generate(0, {"direction": "clockwise"}, demos=3, queries=4)
    episode["train"][0]["output"] = [[0]]
    with pytest.raises(ValueError, match="label"):
        proto.certify(episode)
