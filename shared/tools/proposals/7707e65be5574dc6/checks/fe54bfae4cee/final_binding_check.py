#!/usr/bin/env python3
"""Verify current source binding and owner-style causal-witness replay."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arcpuzzles.catalog import Catalog
from arcpuzzles import parametric_promotion
from arcpuzzles.review_parametric_admission import validate_sequential_witness
from arcpuzzles.review_sequential_replay import replay_witness

TASK_ID = "fe54bfae4cee"


def main() -> int:
    root = Path.cwd().resolve()
    work = root.parent
    checks = work / "checks" / TASK_ID
    qualification = json.loads((checks / "qualification" / "qualification.json").read_text())
    witness = json.loads((checks / "dependency.json").read_text())
    results = json.loads((work / "RESULTS.json").read_text())
    progress = next(row["parametric_work"] for row in results["repair_targets"] if row["task_id"] == TASK_ID)

    contract, binding = parametric_promotion._ready(Catalog(root), TASK_ID)
    if qualification["source_binding"] != binding:
        raise ValueError("qualification source binding differs from current ready source")
    if qualification["contract"] != contract:
        raise ValueError("qualification contract differs from current promotion contract")

    read = lambda name: (work / name).read_bytes()
    witness_validation = validate_sequential_witness(progress, qualification, read)
    replay = replay_witness(root, witness)
    if replay.get("status") != "owner_replayed" or replay.get("evaluations") != 2:
        raise ValueError(f"protected witness replay was incomplete: {replay}")
    if parametric_promotion._ready(Catalog(root), TASK_ID)[1] != binding:
        raise ValueError("source changed during witness replay")

    binding_sha = hashlib.sha256(json.dumps(binding, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    output = {
        "schema": "arcpuzzles-review-final-binding-check-v1",
        "task_id": TASK_ID,
        "status": "pass",
        "source_binding_sha256": binding_sha,
        "contract_matches_qualification": True,
        "source_binding_matches_qualification": True,
        "sequential_witness": witness_validation,
        "owner_style_replay": replay,
        "training_admitted": False,
        "limit": "Reviewer-side current-source verification only; native owner acceptance remains pending.",
    }
    (checks / "final-binding-check.json").write_text(json.dumps(output, sort_keys=True, indent=2) + "\n")
    (checks / "dependency-replay-final.json").write_text(json.dumps(replay, sort_keys=True, indent=2) + "\n")
    print(json.dumps({
        "status": output["status"],
        "source_binding_sha256": binding_sha,
        "witness_cases": witness_validation.get("cases"),
        "racket_evaluations": replay["evaluations"],
        "training_admitted": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
