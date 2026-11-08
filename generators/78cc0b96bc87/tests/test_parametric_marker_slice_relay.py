from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles.catalog import Catalog
from reviewer_support import find_root, public_challenge_bytes


TASK_ID = "78cc0b96bc87"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name: str):
    path = PARAMETRIC / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_{TASK_ID}_{name}_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    root = find_root(__file__)
    catalog = Catalog(root)
    row = catalog.describe(TASK_ID)
    programs = {
        variant["program_solution"]
        for variant in catalog._variants()[row.get("rule_task_id", TASK_ID)]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def _settings(name: str) -> dict[str, str]:
    return {"relay_rule": name}


def _racket_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def test_default_program_is_byte_exact_canonical_and_variant_is_distinct() -> None:
    prototype = _load("prototype")
    canonical = prototype.program(_settings("checkerboard_only"))
    relay = prototype.program(_settings("marker_slice_relay"))
    assert canonical == _canonical_program()
    assert (PARAMETRIC / "canonical.rkt").read_text() == canonical
    assert relay == (PARAMETRIC / "marker_slice_relay.rkt").read_text()
    assert relay != canonical


def test_generation_supports_all_counts_and_inputs_are_setting_matched() -> None:
    prototype = _load("prototype")
    for demos in range(2, 7):
        for queries in range(1, 5):
            seed = 12000 + demos * 10 + queries
            canonical = prototype.generate(seed, _settings("checkerboard_only"), demos, queries)
            relay = prototype.generate(seed, _settings("marker_slice_relay"), demos, queries)
            assert len(canonical["train"]) == len(relay["train"]) == demos
            assert len(canonical["test"]) == len(relay["test"]) == queries
            assert [pair["input"] for pair in canonical["train"] + canonical["test"]] == [
                pair["input"] for pair in relay["train"] + relay["test"]
            ]
            assert len({json.dumps(pair["input"]) for pair in canonical["train"] + canonical["test"]}) == demos + queries
            assert prototype.teaching_check(canonical)["ok"] is True
            assert prototype.teaching_check(relay)["ok"] is True


def test_python_solver_labels_every_pair_and_settings_always_differ() -> None:
    prototype = _load("prototype")
    for seed in (0, 17, 991):
        canonical = prototype.generate(seed, _settings("checkerboard_only"), 3, 4)
        relay = prototype.generate(seed, _settings("marker_slice_relay"), 3, 4)
        for c_pair, r_pair in zip(canonical["train"] + canonical["test"], relay["train"] + relay["test"]):
            assert c_pair["input"] == r_pair["input"]
            assert c_pair["output"] == prototype.solve_python(c_pair["input"], _settings("checkerboard_only"))
            assert r_pair["output"] == prototype.solve_python(r_pair["input"], _settings("marker_slice_relay"))
            assert c_pair["output"] != r_pair["output"]


def test_stage_b_copies_completed_stage_a_slice_not_raw_sparse_input() -> None:
    prototype = _load("prototype")
    episode = prototype.generate(17, _settings("marker_slice_relay"), 2, 4)
    for pair in episode["train"] + episode["test"]:
        facts = prototype.analyze_input(pair["input"])
        stage = prototype.checkerboard_only(pair["input"])
        output = pair["output"]
        assert facts["markers"]
        assert facts["relay_lanes"]
        for lane in facts["relay_lanes"]:
            source = [stage[row][column] for row, column in lane["source"]]
            raw_source = [pair["input"][row][column] for row, column in lane["source"]]
            target = [output[row][column] for row, column in lane["target"]]
            assert target == source
            assert source != raw_source
        assert stage != output


def test_fourth_query_is_substantive_30x30_and_touches_all_boundaries() -> None:
    prototype = _load("prototype")
    episode = prototype.generate(0, _settings("marker_slice_relay"), 3, 4)
    grid = episode["test"][3]["input"]
    output = episode["test"][3]["output"]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert any(value != 0 for value in grid[0])
    assert any(value != 0 for value in grid[-1])
    assert any(row[0] != 0 for row in grid)
    assert any(row[-1] != 0 for row in grid)
    assert sum(value != 0 for row in output for value in row) >= 120
    facts = prototype.analyze_input(grid)
    assert {lane["side"] for lane in facts["relay_lanes"]} == {"left", "right", "up", "down"}


def test_public_turn_is_prefix_stable_and_private_fields_do_not_escape() -> None:
    prototype = _load("prototype")
    full = prototype.generate(314, _settings("marker_slice_relay"), 3, 4)
    short = prototype.generate(314, _settings("marker_slice_relay"), 3, 1)
    assert short["train"] == full["train"]
    assert short["test"] == full["test"][:1]
    first = prototype.public_turn(full, 0)
    last = prototype.public_turn(full, 3)
    assert first["train"] == last["train"] == full["train"]
    assert first["test"] == [{"input": full["test"][0]["input"]}]
    assert last["test"] == [{"input": full["test"][3]["input"]}]
    payload = public_challenge_bytes(first)
    for secret in (b"relay_rule", b"checkerboard_only", b"marker_slice_relay", b"program_solution", b"settings"):
        assert secret not in payload


def test_generation_is_deterministic_fresh_and_rejects_typed_invalid_requests() -> None:
    prototype = _load("prototype")
    episode = prototype.generate(77, _settings("checkerboard_only"), 2, 4)
    replay = prototype.generate(77, _settings("checkerboard_only"), 2, 4)
    assert episode == replay
    assert episode is not replay
    original = copy.deepcopy(replay)
    episode["train"][0]["input"][0][0] = 5
    assert replay == original
    for settings in ({}, {"relay_rule": "unknown"}, {"relay_rule": 1}, {"relay_rule": "checkerboard_only", "extra": True}):
        with pytest.raises(ValueError):
            prototype.generate(0, settings, 2, 4)
    for demos, queries in ((True, 4), (1, 4), (7, 4), (2, True), (2, 0), (2, 5)):
        with pytest.raises(ValueError):
            prototype.generate(0, _settings("checkerboard_only"), demos, queries)


def test_protected_racket_programs_match_python_labels() -> None:
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    prototype = _load("prototype")
    with RacketBridge(timeout=30, startup_timeout=60) as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        for rule in ("checkerboard_only", "marker_slice_relay"):
            episode = prototype.generate(0, _settings(rule), 2, 1)
            wrapped = wrap_rule(prototype.program(_settings(rule)))
            for pair in episode["train"] + episode["test"]:
                actual = bridge.eval_text(f"({wrapped} {_racket_literal(pair['input'])})")
                assert actual == pair["output"]


def test_bounded_shortcut_audit_rejects_plausible_rivals_from_demos() -> None:
    prototype = _load("prototype")
    audit = _load("audit")
    for seed in (0, 17, 91):
        for rule in ("checkerboard_only", "marker_slice_relay"):
            episode = prototype.generate(seed, _settings(rule), 2, 4)
            result = audit.audit_episode(episode, _settings(rule))
            assert result["ambiguous_rivals"] == []
            assert result["demo_survivors"] == []
            assert result["rival_count"] >= 6
