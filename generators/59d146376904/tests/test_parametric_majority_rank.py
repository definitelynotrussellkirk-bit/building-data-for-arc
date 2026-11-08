from __future__ import annotations

import copy
import importlib.util
import json
from functools import cache
from pathlib import Path

import pytest

from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "59d146376904"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def load(filename: str, name: str):
    path = HOME / filename
    assert path.is_file(), f"missing artifact: {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@cache
def proto():
    return load("prototype.py", "_majority_rank_proto")


@cache
def adapter():
    return load("adapter.py", "_majority_rank_adapter")


@cache
def probe():
    return load("adversarial_probe.py", "_majority_rank_probe")


def canonical_program() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError(TASK_ID)


def decisive_grid():
    # 3x3 quadrants. Majority counts are TL=5, TR=8, BL=6, BR=7.
    tl = [[1, 1, 1], [1, 1, 8], [7, 0, 0]]
    tr = [[2, 2, 2], [2, 2, 2], [2, 2, 9]]
    bl = [[3, 3, 3], [3, 3, 3], [1, 2, 0]]
    br = [[4, 4, 4], [4, 4, 4], [4, 5, 0]]
    return [tl[r] + tr[r] for r in range(3)] + [bl[r] + br[r] for r in range(3)]


def test_canonical_program_lookup_is_cached(monkeypatch, tmp_path):
    p = proto()
    source = tmp_path / "canonical.jsonl"
    source.write_text(
        json.dumps({"task_id": TASK_ID, "program_solution": "(rule! identity)"}) + "\n",
        encoding="utf-8",
    )
    calls = 0

    def fake_canonical_path(root):
        nonlocal calls
        calls += 1
        assert root == tmp_path
        return source

    monkeypatch.setattr(p, "canonical_path", fake_canonical_path)
    assert p.canonical_program(root=tmp_path) == "(rule! identity)"
    assert p.canonical_program(root=tmp_path) == "(rule! identity)"
    assert calls == 1


def test_exact_canonical_default_and_distinct_alternate_program():
    p = proto()
    a = adapter()
    assert p.DEFAULT_SETTINGS == {"summary_order": "spatial"}
    assert p.program(p.DEFAULT_SETTINGS) == canonical_program()
    assert a.program(p.DEFAULT_SETTINGS) == canonical_program()
    alternate = {"summary_order": "majority_count_desc"}
    assert p.program(alternate) == a.program(alternate)
    assert p.program(alternate) != canonical_program()


def test_hand_checked_sequential_intermediate_controls_output_order():
    p = proto()
    grid = decisive_grid()
    before = copy.deepcopy(grid)
    facts = p.analyze_input(grid)
    assert [item["majority_count"] for item in facts["quadrants"]] == [5, 8, 6, 7]
    assert facts["majority_rank"] == (1, 3, 2, 0)
    assert p.transform(grid, {"summary_order": "spatial"}) == [[1, 2], [3, 4]]
    assert p.transform(grid, {"summary_order": "majority_count_desc"}) == [[2, 4], [3, 1]]
    assert grid == before


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_inputs_and_settings_are_independent(demos):
    p = proto()
    spatial = p.generate(17, {"summary_order": "spatial"}, demos=demos, queries=4)
    ranked = p.generate(17, {"summary_order": "majority_count_desc"}, demos=demos, queries=4)
    assert len(spatial["train"]) == len(ranked["train"]) == demos
    assert len(spatial["test"]) == len(ranked["test"]) == 4
    left_inputs = [pair["input"] for pair in spatial["train"] + spatial["test"]]
    right_inputs = [pair["input"] for pair in ranked["train"] + ranked["test"]]
    assert left_inputs == right_inputs
    assert len({json.dumps(grid) for grid in left_inputs}) == demos + 4
    assert len(spatial["test"][-1]["input"]) == 30
    assert len(spatial["test"][-1]["input"][0]) == 30
    assert sum(cell != 0 for row in spatial["test"][-1]["input"] for cell in row) >= 600
    for settings, episode in [({"summary_order": "spatial"}, spatial), ({"summary_order": "majority_count_desc"}, ranked)]:
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == p.transform(pair["input"], settings)


def test_constructive_two_demo_lesson_defeats_declared_rivals():
    p = proto()
    for settings in p.SETTINGS:
        episode = p.generate(31, settings, demos=2, queries=4)
        assert p.lesson_rival_survivors(episode["train"], settings) == []
        assert p.query_changing_survivors(episode, settings) == []


def test_public_turn_has_one_input_and_no_private_or_future_fields():
    p = proto()
    episode = p.generate(5, {"summary_order": "majority_count_desc"}, demos=2, queries=4)
    ids = set()
    for index in range(4):
        public = p.public_turn(episode, index)
        assert set(public) == {"train", "test"}
        assert len(public["test"]) == 1
        assert set(public["test"][0]) == {"input"}
        body = public_challenge_bytes(public)
        ids.add(public_challenge_id(public))
        assert b"summary_order" not in body
        assert json.dumps(episode["test"][index]["output"]).encode() not in body
    assert len(ids) == 4


def test_malformed_requests_are_rejected():
    p = proto()
    with pytest.raises(ValueError):
        p.generate(0, {"summary_order": "unknown"}, demos=2, queries=4)
    for bad in (True, 2.0, "2"):
        with pytest.raises((TypeError, ValueError)):
            p.generate(0, {"summary_order": "spatial"}, demos=bad, queries=4)
    bad = decisive_grid()
    bad[0][0] = True
    with pytest.raises(ValueError, match="exact integer"):
        p.analyze_input(bad)


def test_contract_evaluates_with_independent_python_executor():
    p = proto()
    contract = json.loads((HOME / "promotion.json").read_text(encoding="utf-8"))
    programs = {p.program(settings): settings for settings in p.SETTINGS}

    def apply(program, grid):
        return p.transform(grid, programs[program])

    jobs = [
        {"seed": 0, "settings": settings, "demos": 2, "queries": 4}
        for settings in p.SETTINGS
    ]
    report = evaluate_contract(ROOT, TASK_ID, contract, jobs, apply_program=apply)
    assert report["checks"]
    assert all(check["survivors"] == [job["settings"]] for check, job in zip(report["checks"], jobs))


def test_bounded_adversarial_probe_passes():
    report = probe().run_probe(seeds=range(8), demo_counts=(2, 3, 6))
    assert report["status"] == "pass"
    assert report["episodes_checked"] == 8 * 3 * 2
    assert report["query_changing_survivors"] == []
