from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "c953833a3fba"
ROOT = find_root(__file__)
SOURCE = ROOT / f"generators/{TASK_ID}/workspace/parametric/prototype.py"


def _load():
    assert SOURCE.is_file(), "task-local radius prototype is missing"
    spec = importlib.util.spec_from_file_location("parametric_c953_radius", SOURCE)
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


def test_default_program_is_exact_canonical_and_radius_three_changes_shell(proto):
    canonical = _canonical_program()
    assert proto.program({"radius": 2}) == canonical
    alternate = proto.program({"radius": 3})
    assert alternate != canonical
    assert "centers 3 2" in alternate


def test_counts_matched_inputs_demo_identification_and_30x30_stress(proto):
    radius2 = proto.generate(17, {"radius": 2}, demos=3, queries=4)
    radius3 = proto.generate(17, {"radius": 3}, demos=3, queries=4)
    assert _inputs(radius2) == _inputs(radius3)
    assert len(radius2["train"]) == len(radius3["train"]) == 3
    assert len(radius2["test"]) == len(radius3["test"]) == 4
    assert len({proto.digest(grid) for grid in _inputs(radius2)}) == 7
    stress = radius2["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    centers = [(r, c) for r, row in enumerate(stress) for c, value in enumerate(row) if value]
    assert max(r for r, _ in centers) - min(r for r, _ in centers) >= 20
    assert max(c for _, c in centers) - min(c for _, c in centers) >= 20
    assert any(value == 8 for row in stress for value in row)
    assert any(a["output"] != b["output"] for a, b in zip(radius2["train"], radius3["train"]))
    assert radius2["certificate"]["survivors"] == [{"radius": 2}]
    assert radius3["certificate"]["survivors"] == [{"radius": 3}]


@pytest.mark.parametrize("demos", [2, 6])
def test_supported_demo_boundaries_keep_four_queries(proto, demos):
    episode = proto.generate(7, {"radius": 2}, demos=demos, queries=4)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4


def test_real_racket_labels_both_settings_and_demo_only_identification(proto):
    with RacketBridge() as bridge:
        for radius in (2, 3):
            episode = proto.generate(29, {"radius": radius}, demos=3, queries=4)
            for pair in episode["train"] + episode["test"]:
                assert proto.execute_rule(episode["program_solution"], pair["input"], bridge=bridge) == pair["output"]
            cert = proto.certify(episode, execute=lambda source, grid: proto.execute_rule(source, grid, bridge=bridge))
            assert cert["survivors"] == [{"radius": radius}]


def test_public_projection_ignores_private_radius_and_query_answers(proto):
    episode = proto.generate(31, {"radius": 2}, demos=3, queries=4)
    before = public_challenge_bytes(episode)
    assert proto.public_challenge(episode) == json.loads(before)
    assert proto.public_id(episode) == public_challenge_id(episode)
    changed = copy.deepcopy(episode)
    changed["settings"] = {"radius": 3}
    changed["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(changed) == before
    assert proto.public_id(changed) == proto.public_id(episode)


def test_query_prefix_is_independent_of_demo_count(proto):
    single = proto.generate(13, {"radius": 2}, demos=2, queries=1)
    multi = proto.generate(13, {"radius": 2}, demos=6, queries=4)
    assert single["test"] == multi["test"][:1]
    assert proto.public_challenge(single)["test"][0] == proto.public_challenge(multi)["test"][0]


def test_invalid_contracts_and_corrupt_label_fail_closed(proto):
    for overrides in ({"demos": 1}, {"demos": 7}, {"queries": 0}):
        request = {"demos": 3, "queries": 4}
        request.update(overrides)
        with pytest.raises(ValueError):
            proto.generate(0, {"radius": 2}, **request)
    with pytest.raises(ValueError):
        proto.generate(0, {"radius": 4}, demos=3, queries=4)
    episode = proto.generate(0, {"radius": 2}, demos=3, queries=4)
    episode["train"][0]["output"] = [[0]]
    with pytest.raises(ValueError, match="label"):
        proto.certify(episode)
