#!/usr/bin/env python3
"""Replay the invariant-level assertions for both adversarial audit findings."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load(task_id: str, name: str) -> dict:
    return json.loads((ROOT / task_id / name).read_text())


def sha_json(value) -> str:
    raw = json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()


def verify_tied_mode() -> dict:
    task_id = "c0bd45c81959"
    finding = load(task_id, "counterexample.json")
    applied = load(task_id, "racket.json")
    result = applied["results"][0]
    assert finding["self_check_errors"] == []
    assert finding["tied_blocks"]
    tie = finding["tied_blocks"][0]
    counts = sorted(tie["counts"].values(), reverse=True)
    assert counts[:2] == [3, 3]
    assert finding["racket_output"] == result["output"]
    assert finding["racket_output"] != finding["rival_output"]
    assert finding["rival_output_sha256"] == sha_json(finding["rival_output"])
    assert len(finding["disagreement_cells"]) == 1
    return {
        "task_id": task_id,
        "status": "reproduced",
        "seed": finding["seed"],
        "tied_blocks": len(finding["tied_blocks"]),
        "disagreement_cells": len(finding["disagreement_cells"]),
    }


def verify_inner_color_shortcut() -> dict:
    task_id = "1fe4628c64c4"
    finding = load(task_id, "counterexample.json")
    applied = load(task_id, "racket.json")
    result = applied["results"][0]
    assert finding["canonical_pairs_force_inner_equals_horizontal"]
    assert finding["generated_samples_force_inner_equals_horizontal"]
    assert finding["self_check_errors"]
    assert finding["racket_output"] == result["output"]
    assert finding["racket_output"] != finding["rival_output"]
    assert finding["rival_output_sha256"] == sha_json(finding["rival_output"])
    assert finding["disagreement_count"] == len(finding["disagreement_cells"]) == 18
    for row, col in finding["disagreement_cells"]:
        assert finding["racket_output"][row][col] == 5
        assert finding["rival_output"][row][col] == 2
    return {
        "task_id": task_id,
        "status": "reproduced",
        "canonical_pairs_checked": finding["canonical_pairs_checked"],
        "generated_samples_checked": finding["generated_samples_checked"],
        "disagreement_cells": finding["disagreement_count"],
    }


def main() -> None:
    summary = {
        "schema": "arcpuzzles-audit-verification-v1",
        "findings": [verify_tied_mode(), verify_inner_color_shortcut()],
    }
    output = ROOT / "verification-summary.json"
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
