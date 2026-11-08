from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK_ID = "1b39c0e8ebc7"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
PROTOTYPE = HOME / "prototype.py"
ADAPTER = HOME / "adapter.py"
CONTRACT = HOME / "promotion.json"
PROBE = HOME / "adversarial_probe.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def p():
    return _load("_vector_direction_prototype", PROTOTYPE)


@pytest.fixture(scope="module")
def adapter():
    return _load("_vector_direction_adapter", ADAPTER)


def canonical_program() -> str:
    values = []
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            values.append(row["program_solution"])
    assert len(set(values)) == 1
    return values[0]


def all_inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_artifacts_exist_and_default_program_is_exact_canonical(p):
    for path in (PROTOTYPE, ADAPTER, CONTRACT, PROBE):
        assert path.is_file(), path
    assert p.program({"vector_direction": "forward"}) == canonical_program()
    reverse = p.program({"vector_direction": "reverse"})
    assert reverse != canonical_program()
    assert reverse.strip().startswith("(rule!")


def test_matched_inputs_are_deterministic_prefix_stable_and_identifying(p):
    forward = p.generate(41, {"vector_direction": "forward"}, 3, 4)
    reverse = p.generate(41, {"vector_direction": "reverse"}, 3, 4)
    replay = p.generate(41, {"vector_direction": "forward"}, 3, 4)
    assert forward == replay
    assert all_inputs(forward) == all_inputs(reverse)
    assert len({json.dumps(grid, separators=(",", ":")) for grid in all_inputs(forward)}) == 7
    assert all(a["output"] != b["output"] for a, b in zip(forward["train"], reverse["train"]))

    two = p.generate(41, {"vector_direction": "forward"}, 2, 4)
    six = p.generate(41, {"vector_direction": "forward"}, 6, 4)
    assert two["train"] == six["train"][:2]
    assert two["test"] == six["test"]


def test_counts_settings_and_scalar_types_are_strict(p, adapter):
    contract = json.loads(CONTRACT.read_text())
    assert contract["parameters"] == {"vector_direction": ["forward", "reverse"]}
    assert contract["default"] == {"vector_direction": "forward"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [4, 4]}

    claims = adapter.generate(3, {"vector_direction": "reverse"}, 2, 4)
    assert len(claims["train"]) == 2 and len(claims["test"]) == 4
    assert claims["program_solution"] == adapter.program({"vector_direction": "reverse"})

    for args in (
        (True, {"vector_direction": "forward"}, 3, 4),
        (0, {}, 3, 4),
        (0, {"vector_direction": "sideways"}, 3, 4),
        (0, {"vector_direction": "forward", "extra": 1}, 3, 4),
        (0, {"vector_direction": "forward"}, 1, 4),
        (0, {"vector_direction": "forward"}, 7, 4),
        (0, {"vector_direction": "forward"}, 3, 3),
        (0, {"vector_direction": "forward"}, 3, True),
    ):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(*args)


def test_queries_include_substantive_exact_30_square(p):
    episode = p.generate(5, {"vector_direction": "reverse"}, 3, 4)
    dims = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert dims == [(11, 13), (17, 19), (23, 27), (30, 30)]
    large = episode["test"][-1]["input"]
    info = p.analyze_scene(large)
    assert len(info["forward_targets"]) >= 10
    assert len(info["reverse_targets"]) >= 10
    occupied = {(r, c) for r, row in enumerate(large) for c, value in enumerate(row) if value}
    assert len(occupied) >= 56
    assert {0, 29} <= {r for r, _ in occupied}
    assert {0, 29} <= {c for _, c in occupied}
    quadrants = [
        sum((r, c) in occupied for r in rr for c in cc)
        for rr in (range(0, 15), range(15, 30))
        for cc in (range(0, 15), range(15, 30))
    ]
    assert all(count >= 6 for count in quadrants)


def test_public_first_turn_hides_setting_program_answers_and_future_queries(p):
    episode = p.generate(13, {"vector_direction": "reverse"}, 3, 4)
    first = {"train": episode["train"], "test": [{"input": episode["test"][0]["input"]}]}
    visible = public_challenge_bytes(first)
    assert b"reverse" not in visible and b"program_solution" not in visible

    changed = deepcopy(episode)
    changed["program_solution"] = "private"
    for pair in changed["test"]:
        pair["output"] = [[9]]
    changed["test"][1]["input"][0][0] ^= 1
    changed_first = {"train": changed["train"], "test": [{"input": changed["test"][0]["input"]}]}
    assert public_challenge_bytes(changed_first) == visible

    visible_change = deepcopy(first)
    visible_change["test"][0]["input"][0][0] ^= 1
    assert public_challenge_bytes(visible_change) != visible



def test_seed31_two_demo_lesson_refutes_nearest_target_shortcut(p):
    episode = p.generate(31, {"vector_direction": "reverse"}, 2, 4)
    refuted = False
    for pair in episode["train"]:
        info = p.analyze_scene(pair["input"])
        anchor = info["marker_9"]
        targets = sorted(
            info["targets"],
            key=lambda q: (abs(q[0] - anchor[0]) + abs(q[1] - anchor[1]), q),
        )
        shortcut = [[0 for _ in row] for row in pair["input"]]
        for r, c in targets[: len(info["reverse_targets"])]:
            shortcut[r][c] = 7
        refuted |= shortcut != pair["output"]
    assert refuted, "the retained seed-31 nearest-target shortcut must fail a visible demo"

def test_native_worker_executes_racket_and_identifies_both_settings():
    contract = json.loads(CONTRACT.read_text())
    jobs = [
        {"seed": seed, "settings": {"vector_direction": direction}, "demos": 2, "queries": 4}
        for direction in ("forward", "reverse")
        for seed in (0, 17)
    ]
    result = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    assert result["racket"]["backend"] == "racket"
    assert result["racket"]["protected"] is True
    assert [row["survivors"] for row in result["checks"]] == [[job["settings"]] for job in jobs]
    assert result["racket_evaluations"] >= sum(job["demos"] + job["queries"] for job in jobs)


def test_adversarial_probe_rejects_all_declared_shortcuts():
    probe = _load("_vector_direction_probe", PROBE)
    report = probe.run_probe(seeds=range(12), demos=2)
    assert report["episodes"] == 24
    assert report["shortcut_checks"] > 100
    assert report["surviving_shortcuts"] == []
    assert report["crossed_controls"]["passed"] is True
    assert report["smallest_lesson"] == 2
