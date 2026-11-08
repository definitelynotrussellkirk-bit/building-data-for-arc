"""Focused contracts for the anti-diagonal fill / activated-relay family."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK_ID = "d57b7deebba2"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"
PROTOTYPE = PARAMETRIC / "prototype.py"
ADAPTER = PARAMETRIC / "adapter.py"
PROMOTION = PARAMETRIC / "promotion.json"
AUDIT = PARAMETRIC / "audit.py"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing implementation: {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    rows = [
        json.loads(line)
        for line in canonical_path(ROOT).read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    ]
    assert len(rows) == 1
    return rows[0]["program_solution"]


def _run_racket(program: str, grid: list[list[int]]) -> list[list[int]]:
    body = strip_rule_wrapper(program)
    expression = f"({body} g)" if body.lstrip().startswith("(lambda") else body
    bridge = RacketBridge()
    try:
        bridge.define_grid("g", grid)
        return bridge.eval_text(expression)
    finally:
        bridge.shutdown()


def _hand_scene() -> list[list[int]]:
    grid = [[0] * 10 for _ in range(8)]
    grid[1][5] = grid[4][2] = 2
    grid[4][8] = grid[6][6] = 3
    grid[2][5] = 8  # active only after (2,4) is filled
    grid[0][5] = 8  # endpoint-adjacent decoy
    grid[3][8] = 8  # second endpoint-adjacent decoy
    return grid


def _visible_inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_program_is_exact_canonical_and_both_programs_match_literal_hand_case():
    prototype = _load(PROTOTYPE, "relay_program_contract")
    assert prototype.program_for("fill_only") == _canonical_program()

    grid = _hand_scene()
    canonical = deepcopy(grid)
    canonical[2][4] = canonical[3][3] = 2
    canonical[5][7] = 3
    projected = deepcopy(canonical)
    for c in range(5, 10):
        projected[2][c] = 2

    assert prototype.solve_python(grid, "fill_only") == canonical
    assert prototype.solve_python(grid, "activated_projection") == projected
    assert prototype.activation_record(grid) == {
        "relay": [2, 5],
        "newly_filled_neighbor": [2, 4],
        "color": 2,
        "direction": [0, 1],
        "ray_cells": [[2, 6], [2, 7], [2, 8], [2, 9]],
    }
    for setting, expected in (("fill_only", canonical), ("activated_projection", projected)):
        assert _run_racket(prototype.program_for(setting), grid) == expected


def test_adapter_supports_two_to_six_demos_one_to_four_queries_and_matched_inputs():
    adapter = _load(ADAPTER, "relay_adapter_contract")
    prototype = _load(PROTOTYPE, "relay_episode_contract")

    for demos in range(2, 7):
        full = {
            setting: adapter.generate(17, {prototype.PARAMETER_NAME: setting}, demos, 4)
            for setting in prototype.ALLOWED_SETTINGS
        }
        left, right = (full[setting] for setting in prototype.ALLOWED_SETTINGS)
        assert _visible_inputs(left) == _visible_inputs(right)
        assert len(left["train"]) == demos and len(left["test"]) == 4
        assert len({json.dumps(grid, separators=(",", ":")) for grid in _visible_inputs(left)}) == demos + 4
        assert all(a["output"] != b["output"] for a, b in zip(left["train"], right["train"], strict=True))

        for queries in range(1, 5):
            prefix = adapter.generate(17, {prototype.PARAMETER_NAME: "activated_projection"}, demos, queries)
            assert prefix["train"] == full["activated_projection"]["train"]
            assert prefix["test"] == full["activated_projection"]["test"][:queries]

    stress = full["fill_only"]["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    nonzero = {(r, c) for r, row in enumerate(stress) for c, value in enumerate(row) if value}
    assert any(r == 0 for r, _ in nonzero)
    assert any(r == 29 for r, _ in nonzero)
    assert any(c == 0 for _, c in nonzero)
    assert any(c == 29 for _, c in nonzero)
    assert any(r < 15 and c < 15 for r, c in nonzero)
    assert any(r < 15 and c >= 15 for r, c in nonzero)
    assert any(r >= 15 and c < 15 for r, c in nonzero)
    assert any(r >= 15 and c >= 15 for r, c in nonzero)


def test_demonstrations_reject_declared_finite_rivals_and_queries_transfer():
    prototype = _load(PROTOTYPE, "relay_rival_contract")
    for setting in prototype.ALLOWED_SETTINGS:
        episode = prototype.build_claimed_episode(0, setting, 3, 4)
        report = prototype.teaching_report(episode)
        assert report["selected_setting"] == setting
        assert report["demos_identify_declared_setting"] is True
        assert report["all_queries_match_selected"] is True
        assert report["surviving_rivals"] == []
        assert set(report["rejected_rivals"]) == set(prototype.rival_programs(setting))


def test_public_projection_and_sequential_turns_hide_private_fields():
    prototype = _load(PROTOTYPE, "relay_public_contract")
    episode = prototype.build_claimed_episode(23, "activated_projection", 3, 4)
    public = prototype.public_challenge(episode)
    raw = public_challenge_bytes(public)

    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3 and len(public["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    for secret in (b"activated_projection", b"program", b"seed", b"query_answers"):
        assert secret not in raw
    assert prototype.public_id(episode) == hashlib.sha256(raw).hexdigest()

    assert prototype.sequential_turn(episode, 0) == prototype.public_challenge(episode, query_indices=[0])
    for index in range(1, 4):
        assert prototype.sequential_turn(episode, index) == {
            "test": [{"input": episode["test"][index]["input"]}]
        }


def test_validation_rejects_bad_values_and_results_are_fresh_copies():
    adapter = _load(ADAPTER, "relay_validation_contract")
    prototype = _load(PROTOTYPE, "relay_validation_prototype")

    baseline = adapter.generate(3, {prototype.PARAMETER_NAME: "fill_only"}, 2, 4)
    mutated = adapter.generate(3, {prototype.PARAMETER_NAME: "fill_only"}, 2, 4)
    mutated["train"][0]["input"][0][0] = 9
    assert adapter.generate(3, {prototype.PARAMETER_NAME: "fill_only"}, 2, 4) == baseline

    bad_calls = [
        (-1, {prototype.PARAMETER_NAME: "fill_only"}, 2, 4),
        (True, {prototype.PARAMETER_NAME: "fill_only"}, 2, 4),
        (0, {prototype.PARAMETER_NAME: "fill_only"}, 1, 4),
        (0, {prototype.PARAMETER_NAME: "fill_only"}, 7, 4),
        (0, {prototype.PARAMETER_NAME: "fill_only"}, 2, 0),
        (0, {prototype.PARAMETER_NAME: "fill_only"}, 2, 5),
        (0, {prototype.PARAMETER_NAME: "bad"}, 2, 4),
        (0, {prototype.PARAMETER_NAME: "fill_only", "extra": 1}, 2, 4),
    ]
    for args in bad_calls:
        with pytest.raises(ValueError):
            adapter.generate(*args)

    contract = json.loads(PROMOTION.read_text())
    assert contract["default"] == {prototype.PARAMETER_NAME: "fill_only"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}


def test_audit_tool_materializes_protected_racket_and_public_private_evidence(tmp_path):
    audit = _load(AUDIT, "relay_audit_contract")
    report = audit.verify(seed=20261025, out_dir=tmp_path / "evidence", sweep_seeds=1)

    assert report["schema"] == "d57b7deebba2-activated-relay-verification-v1"
    assert report["status"] == "passed"
    assert report["racket"] == {"backend": "racket", "protected": True}
    assert report["counts"]["settings"] == 2
    assert report["counts"]["selected_racket_checked_pairs"] == 14
    assert report["counts"]["racket_program_evaluations"] >= 70
    assert report["matched_inputs_across_settings"] is True
    assert report["maximum_query"]["shape"] == [30, 30]
    assert report["sweep"]["episodes"] == 10
    assert report["sweep"]["failures"] == []

    public_files = sorted((tmp_path / "evidence" / "public").glob("*.json"))
    assert len(public_files) == 2
    for path in public_files:
        assert path.stem == hashlib.sha256(path.read_bytes()).hexdigest()
        payload = json.loads(path.read_text())
        assert set(payload) == {"train", "test"}
        assert all(set(pair) == {"input"} for pair in payload["test"])

    private = json.loads((tmp_path / "evidence" / "private" / "audit.json").read_text())
    assert private["status"] == "passed"
    assert "programs" in private and "settings" in private
