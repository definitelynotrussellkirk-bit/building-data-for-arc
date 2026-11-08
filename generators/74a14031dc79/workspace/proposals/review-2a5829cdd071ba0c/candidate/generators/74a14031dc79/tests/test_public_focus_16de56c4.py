"""Tests for the separate public-evaluation reasoning probe for ARC task 16de56c4."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root

ROOT = find_root(__file__)
TASK_ID = "16de56c4"
EXPECTED_CHALLENGE_SHA256 = "04f2c3b7aed8c16f787c41eb38d771d28bed8c54f4c649596974d8457a24edfd"
SOLVER_PATH = (
    ROOT
    / "generators/74a14031dc79/workspace/public_focus_16de56c4/solver.py"
)
SOURCE_PATH = ROOT / "shared/data/raw/arc-agi_evaluation_challenges.json"


def _load_solver():
    spec = importlib.util.spec_from_file_location("public_focus_16de56c4", SOLVER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _challenge():
    return json.loads(SOURCE_PATH.read_text(encoding="utf-8"))[TASK_ID]


def _grid_sha256(grid) -> str:
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def test_public_focus_source_hash_and_all_training_pairs_replay_exactly():
    solver = _load_solver()
    challenge = _challenge()
    digest = hashlib.sha256(
        json.dumps(challenge, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    assert digest == EXPECTED_CHALLENGE_SHA256 == solver.CHALLENGE_SHA256
    assert [solver.solve(pair["input"]) for pair in challenge["train"]] == [
        pair["output"] for pair in challenge["train"]
    ]


def test_terminal_marker_recolors_the_lattice_and_stops_extension():
    solver = _load_solver()
    grid = [[9, 0, 9, 0, 0, 0, 6, 0, 0]]
    assert solver.solve(grid) == [[6, 0, 6, 0, 6, 0, 6, 0, 0]]


def test_off_lattice_marker_is_preserved_while_anchor_lattice_reaches_edges():
    solver = _load_solver()
    grid = [[9, 0, 9, 5, 0, 0, 0]]
    assert solver.solve(grid) == [[9, 0, 9, 5, 9, 0, 9]]


def test_equal_orientation_evidence_is_rejected_instead_of_guessed():
    solver = _load_solver()
    grid = [
        [1, 1, 0],
        [1, 0, 0],
        [0, 0, 0],
    ]
    with pytest.raises(ValueError, match="orientation"):
        solver.solve(grid)


def test_query_predictions_are_stable_and_source_bound():
    solver = _load_solver()
    challenge = _challenge()
    predictions = [solver.solve(pair["input"]) for pair in challenge["test"]]
    assert [_grid_sha256(grid) for grid in predictions] == [
        "ad2b4472a20a70b73ac1df9bb0bf7884ab3148282568252a440b1268ad5de53a",
        "4d277732077141c6ca67662d6714f4c6bf93bb6866aed9d420610c875ad0c75a",
    ]
    report = solver.solve_challenge(challenge)
    assert report["parent_task_id"] == TASK_ID
    assert report["challenge_sha256"] == EXPECTED_CHALLENGE_SHA256
    assert report["training_pairs_verified"] == 3
    assert report["training_mismatches"] == []
    assert report["query_predictions"] == predictions
    assert report["query_count"] == 2


def test_matching_racket_rule_replays_public_demos_and_four_distinct_queries():
    solver = _load_solver()
    challenge = _challenge()
    query_inputs = solver.four_query_inputs(challenge)
    assert len(query_inputs) == 4
    all_input_hashes = [
        _grid_sha256(pair["input"]) for pair in challenge["train"]
    ] + [_grid_sha256(grid) for grid in query_inputs]
    assert len(all_input_hashes) == len(set(all_input_hashes)) == 7

    source = solver.racket_source()
    assert hashlib.sha256(source.encode()).hexdigest() == solver.RACKET_SOURCE_SHA256
    with RacketBridge() as bridge:
        racket_outputs = solver.execute_racket(
            [pair["input"] for pair in challenge["train"]] + query_inputs,
            bridge=bridge,
        )
        evidence = solver.build_evidence(challenge, bridge=bridge)
    assert racket_outputs[:3] == [pair["output"] for pair in challenge["train"]]
    assert racket_outputs[3:] == [solver.solve(grid) for grid in query_inputs]
    assert evidence["racket"]["source_sha256"] == solver.RACKET_SOURCE_SHA256
    assert evidence["racket"]["labels_checked"] == 7
    assert evidence["sources"] == [
        {
            "path": "generators/74a14031dc79/workspace/public_focus_16de56c4/solver.py",
            "sha256": hashlib.sha256(SOLVER_PATH.read_bytes()).hexdigest(),
        },
        {
            "path": "generators/74a14031dc79/workspace/public_focus_16de56c4/rule.rkt",
            "sha256": solver.RACKET_SOURCE_SHA256,
        },
    ]
    assert evidence["four_query_episode"]["query_count"] == 4
    assert evidence["four_query_episode"]["public_query_count"] == 2
    assert evidence["four_query_episode"]["support_query_count"] == 2
    assert all("output" not in pair for pair in evidence["public_challenge"]["test"])
    assert evidence["four_query_episode"]["test"][:2] == [
        {"input": grid, "output": output}
        for grid, output in zip(query_inputs[:2], racket_outputs[3:5])
    ]


def test_public_focus_cli_returns_success_for_matching_racket_evidence(tmp_path):
    solver = _load_solver()
    out = tmp_path / "prediction.json"
    assert solver.main(["--source", str(SOURCE_PATH), "--out", str(out)]) == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["status"] == "verified_on_public_demonstrations_with_matching_racket"
    assert report["racket"]["labels_checked"] == 7
