#!/usr/bin/env python3
"""Bounded replay of the pinned ba32e05911b0 audit witness."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_path

TICKET_ID = "ticket-18f630737fef41b9"
TASK_ID = "ba32e05911b0"
EXPECTED_SOURCE_SHA256 = "e71e4c26811b60906e4725b9f885f81a27857baeedb267234b8de7be59621345"
EXPECTED_RULE_HASH = "96b86f6cf562"
EXPECTED_ASSETS_SHA256 = "73ea24a0d3d90101d24233c3281ff799a0e40071027bd6ae0f343ae1adfcfb73"
EXPECTED_INDEX_SHA256 = "ce431ffecc71ed23f972eb06b8d24aaf3d506c02c32244a370b56c2e564f9984"
EXPECTED_AUDIT_RECORD_SHA256 = "582f489b76ac3de7fd5aa414024152637e7d90db9bd6074526f754474c95e32d"
EXPECTED_RETURN_ID = "review-42de4260547944fd:v0001"
ROOT = Path(__file__).resolve().parents[3] / "repo"
OUT = Path(__file__).resolve().with_name("result.json")
SOURCE = ROOT / f"generators/{TASK_ID}/generator.py"
AUDIT_ROOT = ROOT / f"generators/{TASK_ID}/counterexamples/review-42de4260547944fd-v0001"
ASSETS = AUDIT_ROOT / "audit_assets.json"
RETAINED = AUDIT_ROOT / f"retained/checks/audit/{TASK_ID}"
INDEX = ROOT / f"generators/{TASK_ID}/evidence/review_index.json"


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def payload_sha(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()


def normalized_rule_hash(program: str) -> str:
    return hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]


def load_generator():
    spec = importlib.util.spec_from_file_location(f"ticket_{TASK_ID}", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    programs = {
        row["program_solution"]
        for row in map(json.loads, canonical_path(ROOT).read_text().splitlines())
        if row.get("task_id") == TASK_ID
    }
    if len(programs) != 1:
        raise AssertionError(f"expected one canonical program, found {len(programs)}")
    return programs.pop()


def grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def execute(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    return bridge.eval_text(f"({strip_rule_wrapper(program)} {grid_literal(grid)})")


def straight_up_rival(grid: list[list[int]]) -> list[list[int]]:
    """Pinned rival: trace the original marker column through every zero, ignoring ledges."""
    original = tuple(map(tuple, grid))
    output = [row[:] for row in grid]
    for marker_row, row in enumerate(original):
        for col, value in enumerate(row):
            if value != 6:
                continue
            for trace_row in range(marker_row - 1, -1, -1):
                if original[trace_row][col] == 0:
                    output[trace_row][col] = 2
            output[0][col] = 6
    return output


def main() -> int:
    source_sha = file_sha(SOURCE)
    assets_sha = file_sha(ASSETS)
    index_sha = file_sha(INDEX)
    assert source_sha == EXPECTED_SOURCE_SHA256
    assert assets_sha == EXPECTED_ASSETS_SHA256
    assert index_sha == EXPECTED_INDEX_SHA256

    index = json.loads(INDEX.read_text())
    audit = next(row for row in index["audits"] if row["return_id"] == EXPECTED_RETURN_ID)
    audit_record_sha = payload_sha(audit)
    assert audit_record_sha == EXPECTED_AUDIT_RECORD_SHA256
    retained = json.loads((RETAINED / "counterexample.json").read_text())
    retained_inputs = json.loads((RETAINED / "input.json").read_text())

    generator = load_generator()
    generated_inputs = [generator.generate(10, index, difficulty="medium") for index in range(4)]
    assert generated_inputs == retained_inputs
    profiles = [generator._analysis(grid)["scene_profile"] for grid in generated_inputs]
    self_check_errors = [generator.self_check(grid, difficulty="medium") for grid in generated_inputs]
    assert profiles == ["clear_climb", "clear_climb", "clear_climb", "long_roll"]
    assert self_check_errors == [[], [], [], []]

    program = canonical_program()
    rule_hash = normalized_rule_hash(program)
    assert rule_hash == EXPECTED_RULE_HASH
    with RacketBridge(max_calls_before_restart=32) as bridge:
        racket_outputs = [execute(bridge, program, grid) for grid in generated_inputs]
    mirror_outputs = [generator.rule_mirror(grid) for grid in generated_inputs]
    assert racket_outputs == mirror_outputs

    rivals = [straight_up_rival(grid) for grid in generated_inputs]
    expected_records = retained["records"]
    input_hashes = [payload_sha(grid) for grid in generated_inputs]
    racket_hashes = [payload_sha(grid) for grid in racket_outputs]
    rival_hashes = [payload_sha(grid) for grid in rivals]
    assert input_hashes == [row["input_sha256"] for row in expected_records]
    assert racket_hashes == [row["racket_output_sha256"] for row in expected_records]
    assert rival_hashes == [row["rival_output_sha256"] for row in expected_records]

    difference_counts = [
        sum(
            actual != rival
            for actual_row, rival_row in zip(actual_grid, rival_grid)
            for actual, rival in zip(actual_row, rival_row)
        )
        for actual_grid, rival_grid in zip(racket_outputs, rivals)
    ]
    demo_fit = [rivals[index] == racket_outputs[index] for index in range(3)]
    query_refuted = rivals[3] != racket_outputs[3]
    assert demo_fit == [True, True, True]
    assert query_refuted
    assert difference_counts == [0, 0, 0, 35]

    report = {
        "schema": "arcpuzzles-ticket-audit-replay-v1",
        "ticket_id": TICKET_ID,
        "type": "audit_replay",
        "status": "completed",
        "consumer": "existing_audit_assessment",
        "scope": "Pinned source/assets plus four generated inputs, one exact Racket program, and one declared rival; no audit resolution or peer battery.",
        "task_id": TASK_ID,
        "return_id": EXPECTED_RETURN_ID,
        "source_path": f"repo/generators/{TASK_ID}/generator.py",
        "source_sha256": source_sha,
        "assets_manifest_sha256": assets_sha,
        "audit_index_sha256": index_sha,
        "audit_record_sha256": audit_record_sha,
        "rule_hash": rule_hash,
        "seed": 10,
        "difficulty": "medium",
        "sample_indices": [0, 1, 2, 3],
        "profiles": profiles,
        "self_check_errors": self_check_errors,
        "input_sha256": input_hashes,
        "racket_output_sha256": racket_hashes,
        "rival_output_sha256": rival_hashes,
        "demo_fit": demo_fit,
        "query_refuted": query_refuted,
        "difference_counts": difference_counts,
        "summary": "Pinned audit witness reproduced exactly: the straight-up rival fits all three clear_climb demonstrations and differs from the long_roll query at 35 cells. This does not clear or create an audit.",
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "demo_fit": demo_fit, "query_difference_count": difference_counts[3]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
