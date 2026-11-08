"""Retain one lawful distributed-extrema witness against endpoint-only bbox."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator

TICKET_ID = "ticket-1d5b90aec909910b"
TASK_ID = "3a4b67ab16ff"
PROBE_SEED = "d608ae470e0e53eaf9f821792b348e2abe27a79b8ccb41684a79674b866f634b"
EXPECTED_SOURCE = "c643621f6d5d606ea6b988bf7d67ec5486ef288c11dc7b0f3fe43a33a611cd31"
EXPECTED_RULE_HASH = "32c694357bd0"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grid_sha(grid) -> str:
    return sha_bytes(json.dumps(grid, separators=(",", ":")).encode())


def main():
    generator, source, source_sha = load_selected_generator(TASK_ID, root=ROOT)
    assert source_sha == EXPECTED_SOURCE
    assert generator.RULE_HASH == EXPECTED_RULE_HASH
    assert "endpoint_only_bbox" in generator.SEMANTIC_RIVALS
    witness_name = "distributed_extrema_refutes_endpoint_only_bbox"
    assert witness_name in generator.SEMANTIC_WITNESSES

    seed = int(PROBE_SEED, 16)
    grid = generator.generate(
        seed,
        0,
        difficulty="medium",
        scene_profile="distributed_extrema",
    )
    original = [row[:] for row in grid]
    errors = generator.self_check(grid, difficulty="medium")
    profile = generator.observe_overrides(grid)
    assert errors == []
    assert profile == {"scene_profile": "distributed_extrema"}
    assert generator.SEMANTIC_WITNESSES[witness_name](grid)

    canonical_python = generator.rule_mirror(grid)
    rival = generator.SEMANTIC_RIVALS["endpoint_only_bbox"](grid)
    assert canonical_python != rival

    canonical_rows = []
    with canonical_path(ROOT).open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                canonical_rows.append(row)
    assert canonical_rows and len({row["program_solution"] for row in canonical_rows}) == 1
    raw_rule = canonical_rows[0]["program_solution"]
    normalized_rule_hash = sha_bytes(" ".join(raw_rule.split()).encode())[:12]
    assert normalized_rule_hash == EXPECTED_RULE_HASH
    wrapped = wrap_rule(raw_rule)

    started = time.monotonic()
    with RacketBridge(timeout=30.0) as bridge:
        racket_version = bridge.eval_text("(version)")
        bridge.eval_text(f"(define ticket-rule {wrapped})")
        bridge.define_grid("ticket-input", grid)
        canonical_racket = bridge.eval_text("(ticket-rule ticket-input)")
    racket_seconds = time.monotonic() - started

    assert canonical_racket == canonical_python
    assert canonical_racket != rival
    assert grid == original

    witness = {
        "schema": "arcpuzzles-adversarial-witness-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "generator_sha256": source_sha,
        "rule_hash": normalized_rule_hash,
        "seed_hex": PROBE_SEED,
        "seed_integer": str(seed),
        "sample_index": 0,
        "difficulty": "medium",
        "scene_profile": "distributed_extrema",
        "shortcut": "endpoint_only_bbox",
        "input": grid,
        "canonical_output": canonical_racket,
        "shortcut_output": rival,
        "input_sha256": grid_sha(grid),
        "canonical_output_sha256": grid_sha(canonical_racket),
        "shortcut_output_sha256": grid_sha(rival),
    }
    (HERE / "witness.json").write_text(json.dumps(witness, indent=2) + "\n")

    report = {
        "schema": "arcpuzzles-ticket-adversarial-witness-v1",
        "ticket_id": TICKET_ID,
        "type": "adversarial_witness",
        "task_id": TASK_ID,
        "status": "completed",
        "source_bound": True,
        "generator_sha256": source_sha,
        "rule_hash": normalized_rule_hash,
        "profile": profile["scene_profile"],
        "validator_errors": errors,
        "shortcut": "endpoint_only_bbox",
        "lawful_witness": True,
        "canonical_racket_matches_python_mirror": canonical_racket == canonical_python,
        "shortcut_refuted": canonical_racket != rival,
        "input_sha256": witness["input_sha256"],
        "canonical_output_sha256": witness["canonical_output_sha256"],
        "shortcut_output_sha256": witness["shortcut_output_sha256"],
        "racket_version": racket_version,
        "racket_elapsed_seconds": racket_seconds,
        "evidence": "checks/tickets/ticket-1d5b90aec909910b/witness.json",
        "disposition": "Current source emits an accepted distributed-extrema lesson that refutes the endpoint-only bounding-box shortcut; no new safety finding.",
        "scope_limit": "One source-bound witness only; no peer battery or profile census was run.",
    }
    (HERE / "result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
