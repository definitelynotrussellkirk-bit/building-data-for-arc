"""Native direct-versus-first-hit relay family for e64c021e29ad."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random

import pytest

from reviewer_support import find_root, public_challenge_bytes

HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
PARAMETRIC = HOME / "workspace" / "parametric"
DIRECT = {"sweep_mode": "all"}
RELAY = {"sweep_mode": "first_hit_relay"}


def load(name="adapter"):
    path = PARAMETRIC / f"{name}.py"
    assert path.is_file(), f"missing {path}"
    spec = importlib.util.spec_from_file_location(f"tested_e64_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def grids(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_exact_selected_authority():
    adapter = load()
    canonical = {
        json.loads(line)["program_solution"]
        for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == HOME.name
    }
    assert canonical == {adapter.program(DIRECT)}
    assert adapter.program(RELAY) != adapter.program(DIRECT)


@pytest.mark.parametrize("demos", range(2, 7))
def test_supported_counts_use_matched_distinct_inputs_and_teach_from_demos(demos):
    adapter, prototype = load(), load("prototype")
    direct = adapter.generate(17, DIRECT, demos, 4)
    relay = adapter.generate(17, RELAY, demos, 4)
    assert len(direct["train"]) == demos and len(direct["test"]) == 4
    assert grids(direct) == grids(relay)
    identities = [json.dumps(grid, separators=(",", ":")) for grid in grids(direct)]
    assert len(identities) == len(set(identities)) == demos + 4
    assert all(
        a["output"] != b["output"]
        for split in ("train", "test")
        for a, b in zip(direct[split], relay[split])
    )
    for settings, episode in ((DIRECT, direct), (RELAY, relay)):
        report = prototype.lesson_report(episode, settings)
        assert report["setting_survivors"] == [settings]
        assert report["surviving_query_disagreements"] == []


def test_query_count_does_not_change_demos_or_first_turn_bytes():
    adapter = load()
    one = adapter.generate(33, RELAY, 3, 1)
    four = adapter.generate(33, RELAY, 3, 4)
    assert one["train"] == four["train"]
    assert one["test"][0] == four["test"][0]
    first = deepcopy(four)
    first["test"] = first["test"][:1]
    assert public_challenge_bytes(one) == public_challenge_bytes(first)


def test_generation_is_deterministic_fresh_and_does_not_touch_global_rng():
    adapter = load()
    state = random.getstate()
    first = adapter.generate(901, RELAY, 3, 4)
    assert random.getstate() == state
    second = adapter.generate(901, RELAY, 3, 4)
    assert first == second and first is not second
    first["train"][0]["input"][0][0] = 9
    assert adapter.generate(901, RELAY, 3, 4) == second


def test_relay_intermediate_is_first_hit_and_supplies_target_code():
    prototype = load("prototype")
    episode = prototype.generate(23, RELAY, 3, 4)
    for pair in episode["train"] + episode["test"]:
        info = prototype.relay_intermediate(pair["input"])
        assert info["hit_color"] in (5, 6, 7, 8)
        assert info["hit_color"] != info["last_hit_color"]
        assert info["target_code"] != info["probe_code"]
        assert info["path_length"] >= 3


def test_fourth_query_is_substantive_30_by_30_stress():
    adapter = load()
    for settings in (DIRECT, RELAY):
        pair = adapter.generate(91, settings, 3, 4)["test"][3]
        grid, output = pair["input"], pair["output"]
        assert (len(grid), len(grid[0])) == (30, 30)
        occupied_in = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
        occupied_out = [(r, c) for r, row in enumerate(output) for c, value in enumerate(row) if value]
        assert len(occupied_in) >= 18
        assert len(occupied_out) >= 30
        assert max(r for r, _ in occupied_in) - min(r for r, _ in occupied_in) >= 20
        assert max(c for _, c in occupied_in) - min(c for _, c in occupied_in) >= 20
        assert max(r for r, _ in occupied_out) - min(r for r, _ in occupied_out) >= 15
        assert max(c for _, c in occupied_out) - min(c for _, c in occupied_out) >= 15


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True}, {"seed": -1}, {"seed": 2**63},
        {"settings": {}}, {"settings": {"sweep_mode": "other"}},
        {"settings": {"sweep_mode": "all", "extra": 1}},
        {"demos": 1}, {"demos": 7}, {"demos": True},
        {"queries": 0}, {"queries": 5}, {"queries": True},
    ],
)
def test_invalid_controls_fail(kwargs):
    adapter = load()
    request = {"seed": 0, "settings": DIRECT, "demos": 3, "queries": 4}
    request.update(kwargs)
    with pytest.raises(ValueError):
        adapter.generate(**request)


def test_direct_audit_rejects_bounding_box_across_the_visible_lesson():
    prototype = load("prototype")
    episode = prototype.generate(17, DIRECT, 3, 4)
    first_prediction = prototype.rival_outputs(episode["train"][0]["input"], DIRECT)[
        "bounding_box_sweep"
    ]
    assert first_prediction == episode["train"][0]["output"]
    report = prototype.lesson_report(episode, DIRECT)
    assert report["equivalent_rivals"] == []
    assert report["rejected_by_demo"]["bounding_box_sweep"] == 1
    assert "bounding_box_sweep" not in report["demo_survivors"]


def test_protected_racket_rules_match_python_and_last_hit_changes_output():
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

    prototype = load("prototype")
    relay_episode = prototype.generate(17, RELAY, 3, 4)
    direct_episode = prototype.generate(17, DIRECT, 3, 4)
    runtime_path = ROOT / "shared/runtime"
    with _local_imports(runtime_path, PARAMETRIC):
        apply, runtime, bridge = _real_evaluator(runtime_path)
        try:
            assert runtime["backend"] == "racket" and runtime["protected"] is True
            for episode, settings in ((direct_episode, DIRECT), (relay_episode, RELAY)):
                for pair in (episode["train"][0], episode["test"][3]):
                    assert apply(prototype.program(settings), deepcopy(pair["input"])) == pair["output"]
            pair = relay_episode["test"][3]
            last_hit_program = (PARAMETRIC / "last_hit.rkt").read_text(encoding="utf-8")
            counterfactual = apply(last_hit_program, deepcopy(pair["input"]))
            assert counterfactual == prototype._relay(pair["input"], target="last")
            assert counterfactual != pair["output"]
        finally:
            bridge.close()


def test_authoring_verifier_job_matrix_covers_native_bounds():
    verifier = load("verify")
    jobs = verifier.jobs()
    assert len(jobs) == 8
    assert {json.dumps(job["settings"], sort_keys=True) for job in jobs} == {
        json.dumps(DIRECT, sort_keys=True), json.dumps(RELAY, sort_keys=True)
    }
    assert {(job["demos"], job["queries"]) for job in jobs} == {(2, 1), (3, 4), (6, 4)}
    for seed in (0, 17):
        for settings in (DIRECT, RELAY):
            assert any(job["seed"] == seed and job["settings"] == settings for job in jobs)


def test_every_authored_racket_source_is_one_complete_expression():
    from arc_repl.parser import Symbol, parse_all

    adapter = load()
    sources = [adapter.program(DIRECT), adapter.program(RELAY),
               (PARAMETRIC / "last_hit.rkt").read_text(encoding="utf-8")]
    for source in sources:
        forms = parse_all(source)
        assert len(forms) == 1
        assert forms[0][0] in (Symbol("rule!"), Symbol("lambda"))
