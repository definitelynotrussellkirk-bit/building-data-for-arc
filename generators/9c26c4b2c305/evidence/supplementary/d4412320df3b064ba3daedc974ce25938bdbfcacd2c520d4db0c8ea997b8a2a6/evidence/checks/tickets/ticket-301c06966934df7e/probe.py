#!/usr/bin/env python3
"""One comparison: advertised grid_w upper boundary, 14 versus 15.

From the packet outer directory:
PYTHONDONTWRITEBYTECODE=1 python3 -B review.py run python3 -B \
    ../checks/tickets/ticket-301c06966934df7e/probe.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time


TICKET_ID = "ticket-301c06966934df7e"
TASK_ID = "9c26c4b2c305"
PINNED_SHA = "8ffed236db06f9606aa5f45c3642e406f9e6293b1b8d678df73db2c318ed1e45"
PINNED_RULE = "e9653f7b4ad7"
TICKET_SEED = "7730d564cba0866c62f35aaa01b10bde8105986756565fe76b69738623382ce8"


def main() -> int:
    started = time.perf_counter()
    repo = Path.cwd()
    source = repo / "generators" / TASK_ID / "generator.py"
    actual_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    if actual_sha != PINNED_SHA:
        raise RuntimeError(f"Pinned generator changed: {actual_sha}")
    spec = importlib.util.spec_from_file_location("ticket_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load pinned generator")
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    if generator.RULE_HASH != PINNED_RULE:
        raise RuntimeError(f"Declared rule hash changed: {generator.RULE_HASH}")

    seed = int(TICKET_SEED, 16)
    cases = []
    for label, width in (("valid_upper_endpoint", 14), ("invalid_above_upper_endpoint", 15)):
        row = {"case": label, "seed": seed, "sample_index": 0,
               "difficulty": None, "overrides": {"grid_w": width}}
        try:
            grid = generator.generate(seed, 0, difficulty=None, grid_w=width)
        except Exception as exc:
            row.update(outcome="raised", exception_type=type(exc).__name__,
                       exception_message=str(exc))
        else:
            row.update(outcome="returned", grid=grid,
                       height=len(grid), row_widths=[len(r) for r in grid])
        cases.append(row)

    passed = (cases[0]["outcome"] == "returned"
              and cases[0]["height"] == 9
              and cases[0]["row_widths"] == [14] * 9
              and cases[1]["outcome"] == "raised"
              and cases[1]["exception_type"] == "ValueError")
    helper = repo / "shared/runtime/puzzle_generators/base.py"
    report = {
        "schema": "bounded-api-boundary-probe-v1",
        "ticket_id": TICKET_ID,
        "consumer": "target_current_audit",
        "task_id": TASK_ID,
        "ticket_seed": TICKET_SEED,
        "seed_conversion": "int(ticket_seed, 16)",
        "source_path": "repo/generators/9c26c4b2c305/generator.py",
        "generator_sha256": actual_sha,
        "rule_hash": generator.RULE_HASH,
        "rule_hash_basis": "Pinned ticket and loaded generator RULE_HASH agree; reference not executed.",
        "shared_helper_sha256": hashlib.sha256(helper.read_bytes()).hexdigest(),
        "effective_cwd": str(repo),
        "advertised_axis": generator.AXES["grid_w"],
        "inspected_boundary": "grid_w integer upper endpoint: 14 accepted; 15 rejected",
        "cases": cases,
        "comparison_passed": passed,
        "payload_elapsed_seconds": time.perf_counter() - started,
        "scope": "Exactly two generate calls at one numeric override boundary. No semantic output claim, other axes, type-coercion review, or general safety assessment.",
        "reference_labels": "Not needed for this API acceptance/rejection comparison; none computed.",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
