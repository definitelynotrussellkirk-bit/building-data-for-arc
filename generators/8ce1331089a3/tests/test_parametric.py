"""Focused contract tests for the native route-action parametric adapter."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "8ce1331089a3"
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1] / "workspace/parametric"


def load_adapter():
    path = HOME / "adapter.py"
    assert path.is_file(), "Native parametric adapter is not implemented"
    name = "_test_8ce_parametric_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def visible_inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_canonical_default_matches_exact_authority_byte_for_byte():
    adapter = load_adapter()
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).open(encoding="utf-8")
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    assert len(programs) == 1
    assert adapter.program({"path_rule": "wall_endpoint"}) == next(iter(programs))
    assert adapter.program({"path_rule": "dominant_trace"}) not in programs


@pytest.mark.parametrize("demos,queries", [(2, 1), (3, 4), (6, 4)])
def test_counts_paired_inputs_distinctness_and_setting_disagreement(demos, queries):
    adapter = load_adapter()
    canonical = adapter.generate(17, {"path_rule": "wall_endpoint"}, demos, queries)
    composed = adapter.generate(17, {"path_rule": "dominant_trace"}, demos, queries)

    assert len(canonical["train"]) == len(composed["train"]) == demos
    assert len(canonical["test"]) == len(composed["test"]) == queries
    assert visible_inputs(canonical) == visible_inputs(composed)
    assert len({json.dumps(grid) for grid in visible_inputs(canonical)}) == demos + queries
    assert all(
        left["output"] != right["output"]
        for left, right in zip(
            canonical["train"] + canonical["test"],
            composed["train"] + composed["test"],
            strict=True,
        )
    )

    for grid in visible_inputs(canonical):
        assert 1 <= len(grid) <= 30
        assert 1 <= len(grid[0]) <= 30
        assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)

    if queries == 4:
        stress = canonical["test"][-1]["input"]
        assert (len(stress), len(stress[0])) == (30, 30)
        interior_nonzero = sum(
            stress[row][col] != 0
            for row in range(1, 29)
            for col in range(1, 29)
        )
        assert interior_nonzero >= 20


def test_two_demos_teach_a_changing_input_derived_dominant_route():
    adapter = load_adapter()
    episode = adapter.generate(0, {"path_rule": "dominant_trace"}, 2, 4)
    analyses = [adapter.analyze(pair["input"]) for pair in episode["train"]]
    assert all(item["unique_dominant"] for item in analyses)
    assert len({item["dominant_route"] for item in analyses}) == 2
    assert all(set(item["route_counts"]) == {"top", "bottom", "left", "right"} for item in analyses)
    assert all(
        pair["output"] == adapter.transform(pair["input"], "dominant_trace")
        for pair in episode["train"] + episode["test"]
    )


def test_generation_is_deterministic_and_prefix_stable_across_counts():
    adapter = load_adapter()
    small = adapter.generate(23, {"path_rule": "dominant_trace"}, 2, 1)
    large = adapter.generate(23, {"path_rule": "dominant_trace"}, 6, 4)
    again = adapter.generate(23, {"path_rule": "dominant_trace"}, 6, 4)
    assert large == again
    assert small["train"] == large["train"][:2]
    assert small["test"][0] == large["test"][0]


def test_public_turn_hides_settings_program_answers_and_future_queries():
    adapter = load_adapter()
    episode = adapter.generate(17, {"path_rule": "dominant_trace"}, 3, 4)
    before = deepcopy(episode)
    first = adapter.public_turn(episode, 0)
    assert set(first) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in first["train"])
    assert len(first["test"]) == 1 and set(first["test"][0]) == {"input"}
    assert first["test"][0]["input"] == episode["test"][0]["input"]
    assert episode == before

    changed = deepcopy(episode)
    changed["seed"] = 999
    changed["settings"] = {"private": "changed"}
    changed["program_solution"] = "PRIVATE CHANGED PROGRAM"
    for pair in changed["test"]:
        pair["output"] = [[9]]
    assert adapter.public_turn(changed, 0) == first
    assert public_challenge_bytes(episode) == public_challenge_bytes(changed)
    assert public_challenge_id(episode) == public_challenge_id(changed)


@pytest.mark.parametrize("index", [-1, 4, True, False, 1.0, "0", None])
def test_public_turn_rejects_non_current_query_indices(index):
    adapter = load_adapter()
    episode = adapter.generate(17, {"path_rule": "dominant_trace"}, 3, 4)
    with pytest.raises(ValueError):
        adapter.public_turn(episode, index)


@pytest.mark.parametrize(
    "settings,demos,queries",
    [
        ({}, 3, 4),
        ({"path_rule": "unknown"}, 3, 4),
        ({"path_rule": True}, 3, 4),
        ({"path_rule": "wall_endpoint", "extra": 1}, 3, 4),
        ({"path_rule": "wall_endpoint"}, 1, 4),
        ({"path_rule": "wall_endpoint"}, 7, 4),
        ({"path_rule": "wall_endpoint"}, 3, 0),
        ({"path_rule": "wall_endpoint"}, 3, 5),
        ({"path_rule": "wall_endpoint"}, True, 4),
    ],
)
def test_invalid_contract_requests_fail_closed(settings, demos, queries):
    adapter = load_adapter()
    with pytest.raises(ValueError):
        adapter.generate(0, settings, demos, queries)


def test_selected_programs_match_claimed_labels_in_protected_racket():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    adapter = load_adapter()
    with RacketBridge(timeout=30, startup_timeout=60) as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        for path_rule in ("wall_endpoint", "dominant_trace"):
            episode = adapter.generate(0, {"path_rule": path_rule}, 2, 4)
            for pair in (episode["train"][0], episode["test"][-1]):
                literal = "'(" + " ".join(
                    "(" + " ".join(map(str, row)) + ")" for row in pair["input"]
                ) + ")"
                actual = bridge.eval_text(
                    f"({wrap_rule(episode['program_solution'])} {literal})"
                )
                assert actual == pair["output"]
