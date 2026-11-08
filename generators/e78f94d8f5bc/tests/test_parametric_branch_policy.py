"""Focused behavior tests for the shortest-path / largest-branch family."""
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

TASK_ID = "e78f94d8f5bc"
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


def _hand_scene() -> list[list[int]]:
    """A detouring tree maze with three off-path branches of sizes 2, 4, 1."""
    grid = [[1] * 9 for _ in range(9)]
    path = (
        [(1, c) for c in range(1, 8)]
        + [(r, 7) for r in range(2, 8)]
        + [(7, c) for c in range(6, 2, -1)]
    )
    branches = [(2, 3), (3, 3), (2, 5), (3, 5), (4, 5), (5, 5), (6, 4)]
    for r, c in path + branches:
        grid[r][c] = 0
    grid[1][1] = 2
    grid[7][3] = 2
    return grid


def _run_racket(program: str, grid: list[list[int]]) -> list[list[int]]:
    body = strip_rule_wrapper(program)
    expression = f"({body} g)" if body.lstrip().startswith("(lambda") else body
    bridge = RacketBridge()
    try:
        bridge.define_grid("g", grid)
        return bridge.eval_text(expression)
    finally:
        bridge.shutdown()


def _visible_inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_program_is_exact_canonical_and_both_programs_match_python_claims():
    prototype = _load(PROTOTYPE, "branch_policy_program_contract")
    assert prototype.program_for("path_only") == _canonical_program()

    grid = _hand_scene()
    for setting in prototype.ALLOWED_SETTINGS:
        expected = prototype.solve_python(grid, setting)
        assert _run_racket(prototype.program_for(setting), grid) == expected


def test_largest_branch_setting_uses_path_as_separator_on_hand_scene():
    prototype = _load(PROTOTYPE, "branch_policy_hand_scene")
    grid = _hand_scene()
    canonical = prototype.solve_python(grid, "path_only")
    branched = prototype.solve_python(grid, "largest_branch")

    assert canonical != branched
    assert {(r, c) for r, row in enumerate(branched) for c, v in enumerate(row) if v == 8} == {
        (2, 5), (3, 5), (4, 5), (5, 5)
    }
    assert all(branched[r][c] == 4 for r, c in [(1, 2), (1, 7), (4, 7), (7, 6)])
    assert branched[1][1] == branched[7][3] == 2


def test_adapter_supports_two_to_six_demos_matched_inputs_and_four_distinct_queries():
    adapter = _load(ADAPTER, "branch_policy_adapter_contract")
    prototype = _load(PROTOTYPE, "branch_policy_episode_contract")

    for demos in range(2, 7):
        episodes = {
            setting: adapter.generate(17, {prototype.PARAMETER_NAME: setting}, demos, 4)
            for setting in prototype.ALLOWED_SETTINGS
        }
        left, right = (episodes[setting] for setting in prototype.ALLOWED_SETTINGS)
        assert _visible_inputs(left) == _visible_inputs(right)
        assert len(left["train"]) == demos
        assert len(left["test"]) == 4
        assert len({json.dumps(grid, separators=(",", ":")) for grid in _visible_inputs(left)}) == demos + 4
        assert all(a["output"] != b["output"] for a, b in zip(left["train"], right["train"], strict=True))

        stress = left["test"][-1]["input"]
        assert (len(stress), len(stress[0])) == (30, 30)
        nonwalls = sum(v != 1 for row in stress for v in row)
        assert nonwalls >= 400
        assert any(stress[r][c] != 1 for r in range(15) for c in range(15))
        assert any(stress[r][c] != 1 for r in range(15) for c in range(15, 30))
        assert any(stress[r][c] != 1 for r in range(15, 30) for c in range(15))
        assert any(stress[r][c] != 1 for r in range(15, 30) for c in range(15, 30))


def test_demonstrations_reject_declared_finite_rivals_and_queries_transfer():
    prototype = _load(PROTOTYPE, "branch_policy_rival_contract")
    for setting in prototype.ALLOWED_SETTINGS:
        episode = prototype.build_claimed_episode(0, setting, 3, 4)
        report = prototype.teaching_report(episode)
        assert report["selected_setting"] == setting
        assert report["all_queries_match_selected"] is True
        assert report["demos_identify_declared_setting"] is True
        assert report["surviving_rivals"] == []
        assert set(report["rejected_rivals"]) == set(prototype.rival_programs(setting))


def test_public_projection_and_sequential_turns_hide_private_fields():
    prototype = _load(PROTOTYPE, "branch_policy_public_contract")
    episode = prototype.build_claimed_episode(23, "largest_branch", 3, 4)
    public = prototype.public_challenge(episode)
    raw = public_challenge_bytes(public)

    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3 and len(public["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert b"largest_branch" not in raw and b"program" not in raw and b"seed" not in raw
    assert prototype.public_id(episode) == hashlib.sha256(raw).hexdigest()

    first = prototype.sequential_turn(episode, 0)
    assert first == prototype.public_challenge(episode, query_indices=[0])
    for index in range(1, 4):
        turn = prototype.sequential_turn(episode, index)
        assert turn == {"test": [{"input": episode["test"][index]["input"]}]}


def test_validation_rejects_bad_api_values_without_mutating_results():
    adapter = _load(ADAPTER, "branch_policy_validation_contract")
    prototype = _load(PROTOTYPE, "branch_policy_validation_prototype")

    good = adapter.generate(3, {prototype.PARAMETER_NAME: "path_only"}, 2, 4)
    snapshot = deepcopy(good)
    good["train"][0]["input"][0][0] = 9
    assert adapter.generate(3, {prototype.PARAMETER_NAME: "path_only"}, 2, 4) == snapshot

    bad_calls = [
        (-1, {prototype.PARAMETER_NAME: "path_only"}, 2, 4),
        (True, {prototype.PARAMETER_NAME: "path_only"}, 2, 4),
        (0, {prototype.PARAMETER_NAME: "path_only"}, 1, 4),
        (0, {prototype.PARAMETER_NAME: "path_only"}, 7, 4),
        (0, {prototype.PARAMETER_NAME: "path_only"}, 2, 3),
        (0, {prototype.PARAMETER_NAME: "bad"}, 2, 4),
        (0, {prototype.PARAMETER_NAME: "path_only", "extra": 1}, 2, 4),
    ]
    for args in bad_calls:
        with pytest.raises(ValueError):
            adapter.generate(*args)

    contract = json.loads(PROMOTION.read_text())
    assert contract["default"] == {prototype.PARAMETER_NAME: "path_only"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [4, 4]}


def test_audit_tool_materializes_racket_backed_public_private_evidence(tmp_path):
    audit = _load(AUDIT, "branch_policy_audit_contract")
    report = audit.verify(seed=20261024, out_dir=tmp_path / "evidence", sweep_seeds=1)

    assert report["schema"] == "e78f94d8f5bc-branch-policy-verification-v1"
    assert report["status"] == "passed"
    assert report["racket"] == {"backend": "racket", "protected": True}
    assert report["counts"]["settings"] == 2
    assert report["counts"]["selected_racket_checked_pairs"] == 14
    assert report["counts"]["racket_program_evaluations"] >= 90
    assert report["matched_inputs_across_settings"] is True
    assert report["maximum_query"]["shape"] == [30, 30]
    assert report["maximum_query"]["nonwall_cells"] >= 400
    assert report["sweep"]["episodes"] == 10
    assert report["sweep"]["failures"] == []

    public_files = sorted((tmp_path / "evidence" / "public").glob("*.json"))
    assert len(public_files) == 2
    for path in public_files:
        assert path.stem == hashlib.sha256(path.read_bytes()).hexdigest()
        challenge = json.loads(path.read_text())
        assert set(challenge) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
        assert all(set(pair) == {"input"} for pair in challenge["test"])

    assert (tmp_path / "evidence" / "private" / "verification.json").is_file()
    assert len(list((tmp_path / "evidence" / "private" / "episodes").glob("*.json"))) == 2
