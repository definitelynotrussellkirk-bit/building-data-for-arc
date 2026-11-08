#!/usr/bin/env python3
"""Combine authoritative labels with the schedule-shortcut outputs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

TASK_ID = "c07088fab0f0"
DIR = Path("../checks/audit") / TASK_ID


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_outputs(receipt):
    if isinstance(receipt, dict):
        for key in ("outputs", "results", "items"):
            value = receipt.get(key)
            if isinstance(value, list):
                if value and isinstance(value[0], dict) and "output" in value[0]:
                    return [item["output"] for item in value]
                return value
        if "output" in receipt:
            value = receipt["output"]
            return value if value and isinstance(value[0], list) and value and isinstance(value[0][0], list) else [value]
    if isinstance(receipt, list):
        if receipt and isinstance(receipt[0], dict) and "output" in receipt[0]:
            return [item["output"] for item in receipt]
        return receipt
    raise ValueError("unrecognized apply receipt")


def main() -> None:
    meta = json.loads((DIR / "metadata.json").read_text())
    inputs = json.loads((DIR / "input.json").read_text())
    rivals = json.loads((DIR / "rival.json").read_text())
    receipt = json.loads((DIR / "racket.json").read_text())
    outputs = extract_outputs(receipt)
    assert len(inputs) == len(rivals) == len(outputs) == 5
    matches = [rival == actual for rival, actual in zip(rivals, outputs)]
    assert matches == [True, True, True, True, False], matches
    report = {
        **meta,
        "status": "reproduced_schedule_shortcut",
        "generator_sha256": sha(Path("generators") / TASK_ID / "generator.py"),
        "input_sha256": sha(DIR / "input.json"),
        "racket_receipt": "checks/audit/c07088fab0f0/racket.json",
        "rival_matches_authority": matches,
        "counterexample_input": inputs[4],
        "actual_racket_output": outputs[4],
        "rival_output": rivals[4],
        "command": [
            "python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply",
            TASK_ID, "--input", "../checks/audit/c07088fab0f0/input.json",
            "--out", "../checks/audit/c07088fab0f0/racket.json",
        ],
        "cwd": "packet_root",
    }
    (DIR / "finding.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "matches": matches,
        "counterexample_actual": outputs[4],
        "counterexample_rival": rivals[4],
    }, indent=2))


if __name__ == "__main__":
    main()
