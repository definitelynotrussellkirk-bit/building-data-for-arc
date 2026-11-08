"""Behavioral and adversarial tests for the size-to-marker echo family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK_ID = "01f4294de005"
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
PROTOTYPE = PARAMETRIC / "prototype.py"
CONTRACT = PARAMETRIC / "promotion.json"


def _load():
    assert PROTOTYPE.is_file(), f"missing parametric prototype: {PROTOTYPE}"
    spec = importlib.util.spec_from_file_location("_size_marker_echo_subject", PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def p():
    return _load()


def _canonical_program():
    programs = {
        row["program_solution"]
        for row in map(json.loads, canonical_path(ROOT).read_text().splitlines())
        if row.get("task_id") == TASK_ID
    }
    assert len(programs) == 1
    return programs.pop()


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_byte_exact_canonical_and_alternative_is_complete(p):
    direct = p.program({"echo_mode": "none"})
    echo = p.program({"echo_mode": "matching_marker"})
    assert direct == _canonical_program()
    assert echo != direct
    assert echo.strip().startswith("(rule!")


def test_inputs_are_setting_neutral_distinct_prefix_stable_and_identifying(p):
    direct = p.generate(41, {"echo_mode": "none"}, 3, 4)
    echo = p.generate(41, {"echo_mode": "matching_marker"}, 3, 4)
    assert _inputs(direct) == _inputs(echo)
    assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(direct)}) == 7
    assert all(a["output"] != b["output"] for a, b in zip(direct["train"], echo["train"]))

    two = p.generate(41, {"echo_mode": "matching_marker"}, 2, 4)
    six = p.generate(41, {"echo_mode": "matching_marker"}, 6, 4)
    one = p.generate(41, {"echo_mode": "matching_marker"}, 3, 1)
    assert two["train"] == six["train"][:2]
    assert two["test"] == six["test"]
    assert one["train"] == echo["train"]
    assert one["test"] == echo["test"][:1]


def test_each_scene_has_complete_size_palette_and_unique_matching_markers(p):
    for split, count in (("train", 6), ("test", 4)):
        for index in range(count):
            grid = p.sample_input(73, split, index)
            facts = p.analyze_scene(grid)
            n = len(facts["palette"])
            assert sorted(len(component) for component in facts["orange_components"]) == list(range(1, n + 1))
            assert {marker["color"] for marker in facts["markers"]} == set(facts["palette"])
            assert len(facts["markers"]) == n
            assert all(len(marker["cells"]) == 1 for marker in facts["markers"])
            assert p.apply_rule(grid, "none") != p.apply_rule(grid, "matching_marker")


def test_minimum_two_demo_lesson_defeats_relevant_bypass_rules(p):
    episode = p.generate(117, {"echo_mode": "matching_marker"}, 2, 4)
    survivors = []
    for name in p.RIVAL_NAMES:
        if all(
            p.apply_rival(pair["input"], name) == pair["output"]
            for pair in episode["train"]
        ):
            survivors.append(name)
    assert survivors == []


def test_queries_cover_minimum_large_and_boundary_spanning_geometry(p):
    episode = p.generate(5, {"echo_mode": "matching_marker"}, 3, 4)
    dims = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert dims == [(9, 12), (16, 20), (23, 27), (30, 30)]
    large = episode["test"][-1]["input"]
    occupied = {(r, c) for r, row in enumerate(large) for c, value in enumerate(row) if value}
    assert {0, 29} <= {r for r, _ in occupied}
    assert {0, 29} <= {c for _, c in occupied}
    quadrants = [
        sum((r, c) in occupied for r in rr for c in cc)
        for rr in (range(0, 15), range(15, 30))
        for cc in (range(0, 15), range(15, 30))
    ]
    assert all(value > 0 for value in quadrants)
    assert len(occupied) >= 45


def test_public_first_turn_is_count_stable_and_contains_no_private_fields(p):
    four = p.generate(19, {"echo_mode": "matching_marker"}, 3, 4)
    one = p.generate(19, {"echo_mode": "matching_marker"}, 3, 1)
    public_four = public_challenge_bytes(
        {"train": four["train"], "test": [{"input": four["test"][0]["input"]}]}
    )
    public_one = public_challenge_bytes(
        {"train": one["train"], "test": [{"input": one["test"][0]["input"]}]}
    )
    assert public_four == public_one
    assert b"matching_marker" not in public_four
    assert b"program_solution" not in public_four
    assert set(json.loads(public_four)["test"][0]) == {"input"}


def test_native_worker_executes_both_programs_and_identifies_minimum_lessons():
    contract = json.loads(CONTRACT.read_text())
    jobs = [
        {"seed": seed, "settings": {"echo_mode": mode}, "demos": 2, "queries": 4}
        for seed in (0, 17)
        for mode in ("none", "matching_marker")
    ]
    result = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    assert result["racket"]["backend"] == "racket"
    assert result["racket"]["protected"] is True
    assert [row["survivors"] for row in result["checks"]] == [[job["settings"]] for job in jobs]
    assert any(
        len(pair["input"]) == 30 and len(pair["input"][0]) == 30
        for episode in result["episodes"]
        for pair in episode["test"]
    )


@pytest.mark.parametrize(
    "patch",
    [
        {"seed": True},
        {"seed": -1},
        {"demos": 1},
        {"demos": 7},
        {"demos": 2.0},
        {"queries": 0},
        {"queries": 5},
        {"queries": True},
        {"settings": {}},
        {"settings": {"echo_mode": "nearest"}},
        {"settings": {"echo_mode": "none", "extra": 1}},
    ],
)
def test_invalid_requests_and_boolean_cells_are_rejected(p, patch):
    args = {"seed": 0, "settings": {"echo_mode": "none"}, "demos": 3, "queries": 4}
    args.update(patch)
    with pytest.raises((TypeError, ValueError)):
        p.generate(**args)

    malformed = p.sample_input(0, "train", 0)
    malformed[1][0] = False
    with pytest.raises(ValueError):
        p.apply_rule(malformed, "none")
