#!/usr/bin/env python3
"""Build the admission-schema causal witness from exact qualified source.

This adapter converts the richer task-local self-audit witness into the
repository's owner-replay contract.  It embeds the exact qualified setting
program, the exact counterfactual program, and the qualification's complete
source binding, then performs the same protected-Racket replay used by owner
admission before writing either artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
WORK = Path(__file__).resolve().parents[2]
REPO = WORK / "repo"
for candidate in (REPO / "src", REPO / "shared" / "runtime"):
    text = str(candidate)
    if text not in sys.path:
        sys.path.insert(0, text)

from arcpuzzles.review_sequential_replay import replay_witness  # noqa: E402

TASK_ID = "4e05481a2c21"
SETTING = {"pack_order": "hole_area_descending"}


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def _compact(value: Any) -> bytes:
    return (json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ) + "\n").encode("utf-8")


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _difference_cells(left: list[list[int]], right: list[list[int]]) -> int:
    if len(left) != len(right):
        raise ValueError("counterfactual output height changed")
    if any(len(a) != len(b) for a, b in zip(left, right, strict=True)):
        raise ValueError("counterfactual output width changed")
    return sum(
        a != b
        for row_a, row_b in zip(left, right, strict=True)
        for a, b in zip(row_a, row_b, strict=True)
    )


def build() -> tuple[dict[str, Any], dict[str, Any]]:
    qualification_path = HERE / "qualification" / "qualification.json"
    prior_path = HERE / "self-audit-final" / "sequential-witness.json"
    results_path = WORK / "RESULTS.json"
    qualification = _read_json(qualification_path)
    prior = _read_json(prior_path)
    results = _read_json(results_path)

    targets = results.get("repair_targets")
    if not isinstance(targets, list):
        raise ValueError("RESULTS.json has no repair_targets list")
    target = next((row for row in targets if row.get("task_id") == TASK_ID), None)
    if not isinstance(target, dict):
        raise ValueError(f"RESULTS.json has no target {TASK_ID}")
    dependency = target.get("parametric_work", {}).get("sequential_dependency")
    if not isinstance(dependency, dict):
        raise ValueError("RESULTS.json has no MAIN sequential dependency")

    program_path = REPO / "generators" / TASK_ID / "workspace" / "parametric" / "hole_area_descending.rkt"
    counterfactual_path = REPO / "generators" / TASK_ID / "workspace" / "parametric" / "bbox_area_descending.rkt"
    program = program_path.read_text()
    counterfactual_program = counterfactual_path.read_text()

    setting_key = json.dumps(
        SETTING,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    qualified_hash = qualification.get("programs", {}).get(setting_key)
    actual_hash = _sha_bytes(program.encode())
    if actual_hash != qualified_hash:
        raise ValueError(
            f"setting program drifted: qualified={qualified_hash}, actual={actual_hash}"
        )
    if prior.get("correct_program_sha256") != actual_hash:
        raise ValueError("prior self-audit does not bind the qualified program")
    counterfactual_hash = _sha_bytes(counterfactual_program.encode())
    if prior.get("counterfactual_program_sha256") != counterfactual_hash:
        raise ValueError("prior self-audit counterfactual source drifted")

    output = prior.get("correct_output")
    counterfactual_output = prior.get("counterfactual_output")
    if not isinstance(output, list) or not isinstance(counterfactual_output, list):
        raise ValueError("prior witness is missing output grids")
    different_cells = _difference_cells(output, counterfactual_output)
    if different_cells != prior.get("different_cells") or different_cells <= 0:
        raise ValueError("reported counterfactual difference is stale")

    witness: dict[str, Any] = {
        "schema": "arcpuzzles-sequential-dependency-witness-v1",
        "task_id": TASK_ID,
        "source_binding": qualification["source_binding"],
        "racket": {"backend": "racket", "protected": True},
        "step_a": dependency["step_a"],
        "intermediate": dependency["intermediate"],
        "step_b": dependency["step_b"],
        "why_b_depends_on_a": dependency["why_b_depends_on_a"],
        "cases": [
            {
                "input": prior["input"],
                "settings": SETTING,
                "intermediate_value": prior["intermediate"],
                "output": output,
                "counterfactual_output": counterfactual_output,
                "ablation": "wrong_intermediate",
                "program": program,
                "counterfactual_program": counterfactual_program,
                "counterfactual": prior.get("counterfactual"),
                "different_cells": different_cells,
            }
        ],
        "construction": {
            "qualification_sha256": _sha_bytes(qualification_path.read_bytes()),
            "prior_witness_sha256": _sha_bytes(prior_path.read_bytes()),
            "qualified_program_sha256": actual_hash,
            "counterfactual_program_sha256": counterfactual_hash,
            "limits": "One bounded authored counterfactual; not a universal depth proof.",
        },
    }

    replay = replay_witness(REPO, witness)
    identity = replay.get("racket", {})
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        raise RuntimeError("construction replay did not use protected Racket")
    if replay.get("status") != "owner_replayed" or replay.get("evaluations") != 2:
        raise RuntimeError(f"unexpected replay result: {replay}")
    replay_cases = replay.get("cases")
    if not isinstance(replay_cases, list) or len(replay_cases) != 1:
        raise RuntimeError("construction replay did not return one case")
    if replay_cases[0].get("program_sha256") != actual_hash:
        raise RuntimeError("construction replay used the wrong qualified program")
    if replay_cases[0].get("counterfactual_program_sha256") != counterfactual_hash:
        raise RuntimeError("construction replay used the wrong counterfactual program")

    return witness, replay


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--replay-out", type=Path, required=True)
    args = parser.parse_args()

    witness, replay = build()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.replay_out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(_compact(witness))
    args.replay_out.write_bytes(_compact(replay))
    print(json.dumps({
        "status": "passed",
        "witness": str(args.out),
        "witness_sha256": _sha_bytes(args.out.read_bytes()),
        "replay": str(args.replay_out),
        "replay_sha256": _sha_bytes(args.replay_out.read_bytes()),
        "cases": len(witness["cases"]),
        "protected_racket_evaluations": replay["evaluations"],
        "different_cells": witness["cases"][0]["different_cells"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
