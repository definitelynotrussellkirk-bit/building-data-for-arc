from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "7bd583886bad"
ROOT = find_root(__file__)
SOURCE = ROOT / f"generators/{TASK_ID}/workspace/parametric/prototype.py"


def _load():
    assert SOURCE.is_file(), "task-local label-policy prototype is missing"
    spec = importlib.util.spec_from_file_location("parametric_7bd_label_policy", SOURCE)
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


def test_default_program_is_exact_canonical_and_area_policy_changes_only_label(proto):
    canonical = _canonical_program()
    assert proto.program({"label_mode": "shape_type"}) == canonical
    alternate = proto.program({"label_mode": "area"})
    assert alternate != canonical
    assert "(paint-cells acc (snd piece) (length (snd piece)))" in alternate


def test_counts_matched_inputs_demo_identification_and_spanning_30x30(proto):
    by_type = proto.generate(17, {"label_mode": "shape_type"}, demos=3, queries=4)
    by_area = proto.generate(17, {"label_mode": "area"}, demos=3, queries=4)
    assert _inputs(by_type) == _inputs(by_area)
    assert len(by_type["train"]) == len(by_area["train"]) == 3
    assert len(by_type["test"]) == len(by_area["test"]) == 4
    assert len({proto.digest(grid) for grid in _inputs(by_type)}) == 7
    stress = by_type["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    analysis = proto.analyze_mask(stress)
    assert analysis["connected"]
    assert analysis["cover_count"] == 1
    assert analysis["bbox_height"] >= 25
    assert analysis["bbox_width"] >= 25
    assert analysis["cell_count"] >= 70
    assert any(a["output"] != b["output"] for a, b in zip(by_type["train"], by_area["train"]))
    assert by_type["certificate"]["survivors"] == [{"label_mode": "shape_type"}]
    assert by_area["certificate"]["survivors"] == [{"label_mode": "area"}]


@pytest.mark.parametrize("demos", [2, 6])
def test_supported_demo_boundaries_keep_four_queries(proto, demos):
    episode = proto.generate(5, {"label_mode": "shape_type"}, demos=demos, queries=4)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4


def test_real_racket_labels_both_settings_including_30x30(proto):
    with RacketBridge(timeout=60) as bridge:
        for mode in ("shape_type", "area"):
            episode = proto.generate(23, {"label_mode": mode}, demos=3, queries=4)
            for pair in episode["train"] + episode["test"]:
                assert proto.execute_rule(episode["program_solution"], pair["input"], bridge=bridge) == pair["output"]
            cert = proto.certify(episode, execute=lambda source, grid: proto.execute_rule(source, grid, bridge=bridge))
            assert cert["survivors"] == [{"label_mode": mode}]


def test_public_projection_ignores_private_policy_and_query_answers(proto):
    episode = proto.generate(31, {"label_mode": "shape_type"}, demos=3, queries=4)
    before = public_challenge_bytes(episode)
    assert proto.public_challenge(episode) == json.loads(before)
    assert proto.public_id(episode) == public_challenge_id(episode)
    changed = copy.deepcopy(episode)
    changed["settings"] = {"label_mode": "area"}
    changed["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(changed) == before
    assert proto.public_id(changed) == proto.public_id(episode)


def test_query_prefix_is_independent_of_demo_count(proto):
    single = proto.generate(13, {"label_mode": "shape_type"}, demos=2, queries=1)
    multi = proto.generate(13, {"label_mode": "shape_type"}, demos=6, queries=4)
    assert single["test"] == multi["test"][:1]
    assert proto.public_challenge(single)["test"][0] == proto.public_challenge(multi)["test"][0]


def test_invalid_contracts_and_corrupt_label_fail_closed(proto):
    for overrides in ({"demos": 1}, {"demos": 7}, {"queries": 0}):
        request = {"demos": 3, "queries": 4}
        request.update(overrides)
        with pytest.raises(ValueError):
            proto.generate(0, {"label_mode": "shape_type"}, **request)
    with pytest.raises(ValueError):
        proto.generate(0, {"label_mode": "greedy"}, demos=3, queries=4)
    episode = proto.generate(0, {"label_mode": "shape_type"}, demos=3, queries=4)
    episode["train"][0]["output"] = [[0]]
    with pytest.raises(ValueError, match="label"):
        proto.certify(episode)
