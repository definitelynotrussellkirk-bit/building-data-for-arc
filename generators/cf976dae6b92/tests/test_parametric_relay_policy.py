"""Behavioral tests for the fixed/nearest relay routing family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import canonical_path, find_root, public_challenge_bytes

ROOT = find_root(__file__)
TASK_ID = "cf976dae6b92"
HOME = ROOT / f"generators/{TASK_ID}/workspace/parametric"
PROTOTYPE = HOME / "prototype.py"
ADAPTER = HOME / "adapter.py"
CONTRACT = HOME / "promotion.json"
PROBE = HOME / "adversarial_probe.py"


def _load(name: str, path: Path):
    assert path.is_file(), f"missing runnable artifact: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def proto():
    return _load("cf976dae6b92_parametric", PROTOTYPE)


@pytest.fixture(scope="module")
def adapter():
    return _load("cf976dae6b92_adapter", ADAPTER)


@pytest.fixture(scope="module")
def probe():
    return _load("cf976dae6b92_probe", PROBE)


def _canonical_program() -> str:
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()]
    programs = {row["program_solution"] for row in rows if row.get("task_id") == TASK_ID}
    assert len(programs) == 1
    return programs.pop()


def _decisive_grid() -> list[list[int]]:
    grid = [[0 for _ in range(7)] for _ in range(7)]
    grid[0][0] = 2
    grid[5][1] = 3
    grid[3][4] = 4
    return grid


def test_artifacts_and_exact_canonical_default(proto, adapter):
    assert ADAPTER.is_file() and CONTRACT.is_file() and PROBE.is_file()
    expected = _canonical_program()
    assert proto.DEFAULT_SETTINGS == {"relay_policy": "fixed_4"}
    assert proto.program(proto.DEFAULT_SETTINGS) == expected
    assert adapter.program(proto.DEFAULT_SETTINGS) == expected
    assert proto.program({"relay_policy": "nearest_to_2"}) != expected


def test_decisive_nearest_relay_has_hand_checked_outputs(proto):
    grid = _decisive_grid()
    fixed = [
        [2, 5, 5, 5, 5, 0, 0],
        [0, 0, 0, 0, 5, 0, 0],
        [0, 0, 0, 0, 5, 0, 0],
        [0, 5, 5, 5, 4, 0, 0],
        [0, 5, 0, 0, 0, 0, 0],
        [0, 3, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]
    nearest = [
        [2, 5, 0, 0, 0, 0, 0],
        [0, 5, 0, 0, 0, 0, 0],
        [0, 5, 0, 0, 0, 0, 0],
        [0, 5, 0, 0, 4, 0, 0],
        [0, 5, 0, 0, 5, 0, 0],
        [0, 3, 5, 5, 5, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]
    before = copy.deepcopy(grid)
    assert proto.relay_choice(grid, "nearest_to_2") == 3
    assert proto.apply_rule(grid, "fixed_4") == fixed
    assert proto.apply_rule(grid, "nearest_to_2") == nearest
    assert grid == before


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_are_independent_inputs_distinct_and_settings_matched(proto, demos):
    fixed = proto.generate(17, {"relay_policy": "fixed_4"}, demos=demos, queries=4)
    near = proto.generate(17, {"relay_policy": "nearest_to_2"}, demos=demos, queries=4)
    assert len(fixed["train"]) == demos and len(fixed["test"]) == 4
    assert [p["input"] for p in fixed["train"] + fixed["test"]] == [
        p["input"] for p in near["train"] + near["test"]
    ]
    encoded = [
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in fixed["train"] + fixed["test"]
    ]
    assert len(encoded) == len(set(encoded))
    short = proto.generate(17, {"relay_policy": "fixed_4"}, demos=2, queries=4)
    assert short["train"] == fixed["train"][:2]
    assert short["test"] == fixed["test"]


def test_minimum_lesson_crosses_selector_and_nuisance_controls(proto):
    episode = proto.generate(23, {"relay_policy": "nearest_to_2"}, demos=2, queries=4)
    choices = [proto.relay_choice(pair["input"], "nearest_to_2") for pair in episode["train"]]
    assert choices == [3, 4]
    assert len({(len(pair["input"]), len(pair["input"][0])) for pair in episode["train"]}) == 1
    fixed = proto.generate(23, {"relay_policy": "fixed_4"}, demos=2, queries=4)
    assert fixed["train"][0]["output"] != episode["train"][0]["output"]
    assert fixed["train"][1]["output"] == episode["train"][1]["output"]
    assert proto.lesson_rival_survivors(episode["train"], "nearest_to_2") == []
    assert proto.lesson_rival_survivors(fixed["train"], "fixed_4") == []


def test_query_bank_contains_boundary_and_substantive_30x30_stress(proto):
    episode = proto.generate(31, {"relay_policy": "nearest_to_2"}, demos=3, queries=4)
    assert any(
        len(pair["input"]) == 7 or len(pair["input"][0]) == 7
        for pair in episode["test"]
    )
    large = next(
        pair for pair in episode["test"]
        if len(pair["input"]) == 30 and len(pair["input"][0]) == 30
    )
    nonzero = {(r, c) for r, row in enumerate(large["output"]) for c, v in enumerate(row) if v}
    gray = {(r, c) for r, row in enumerate(large["output"]) for c, v in enumerate(row) if v == 5}
    assert len(gray) >= 60
    assert min(r for r, _ in nonzero) == 0 or max(r for r, _ in nonzero) == 29
    assert min(c for _, c in nonzero) == 0 or max(c for _, c in nonzero) == 29
    assert len({r // 15 for r, _ in gray}) == 2
    assert len({c // 15 for _, c in gray}) == 2


def test_public_first_turn_excludes_private_and_future_data(proto):
    episode = proto.generate(41, {"relay_policy": "nearest_to_2"}, demos=3, queries=4)
    first = proto.public_turn(episode, 0)
    body = public_challenge_bytes(first)
    assert set(first) == {"train", "test"}
    assert len(first["test"]) == 1 and set(first["test"][0]) == {"input"}
    changed = copy.deepcopy(episode)
    changed["settings"] = {"relay_policy": "fixed_4"}
    changed["program_solution"] = "private"
    changed["test"][0]["output"] = [[9]]
    changed["test"][3]["input"] = [[9]]
    assert public_challenge_bytes(proto.public_turn(changed, 0)) == body


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True}, {"seed": 1.0}, {"demos": 1}, {"demos": 7},
        {"demos": True}, {"queries": 3}, {"queries": 5}, {"queries": True},
        {"settings": {}}, {"settings": {"relay_policy": "bad"}},
        {"settings": {"relay_policy": "fixed_4", "extra": 1}},
    ],
)
def test_invalid_requests_are_rejected(proto, kwargs):
    request = dict(seed=0, settings=proto.DEFAULT_SETTINGS, demos=3, queries=4)
    request.update(kwargs)
    with pytest.raises((TypeError, ValueError)):
        proto.generate(**request)


def test_tied_nearest_scene_is_outside_admitted_grammar(proto):
    grid = [[0 for _ in range(7)] for _ in range(7)]
    grid[3][3] = 2
    grid[1][2] = 3  # distance 3
    grid[5][4] = 4  # distance 3
    with pytest.raises(ValueError, match="unequal Manhattan"):
        proto.relay_choice(grid, "nearest_to_2")


def test_native_worker_replays_racket_and_identifies_both_settings():
    contract = json.loads(CONTRACT.read_text())
    jobs = [
        {"seed": seed, "settings": {"relay_policy": policy}, "demos": 2, "queries": 4}
        for seed in (0, 17)
        for policy in ("fixed_4", "nearest_to_2")
    ]
    result = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    assert result["racket"]["backend"] == "racket"
    assert result["racket"]["protected"] is True
    assert [row["survivors"] for row in result["checks"]] == [[job["settings"]] for job in jobs]
    assert any(
        len(pair["input"]) == 30 and len(pair["input"][0]) == 30
        for episode in result["episodes"] for pair in episode["test"]
    )


def test_bounded_adversarial_probe_attacks_minimum_lesson(probe):
    report = probe.run_probe(seeds=range(8), demo_counts=(2, 3, 6))
    assert report["status"] == "pass"
    assert report["episodes_checked"] == 8 * 3 * 2
    assert report["query_changing_survivors"] == []
    assert report["max_input_shape"] == [30, 30]
    assert report["relay_choices"] == [3, 4]
