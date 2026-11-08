#!/usr/bin/env python3
"""Compare predecessor/current visible evidence for task 506e262f9354."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
TASK = "506e262f9354"
BASELINE_EVIDENCE = HERE / "baseline-seed-1"
CURRENT_EVIDENCE = HERE / "current-seed-1"
BASELINE_PROTOTYPE = (
    WORK / ".review/baseline/repo/generators" / TASK / "workspace/parametric/prototype.py"
)
CURRENT_PROTOTYPE = (
    WORK / "repo/generators" / TASK / "workspace/parametric/prototype.py"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def public_rows(root: Path) -> list[dict[str, object]]:
    return [
        {"name": path.name, "sha256": sha256(path), "bytes": path.stat().st_size}
        for path in sorted((root / "public").glob("*.json"))
    ]


def main() -> int:
    baseline_rows = public_rows(BASELINE_EVIDENCE)
    current_rows = public_rows(CURRENT_EVIDENCE)
    report = json.loads((CURRENT_EVIDENCE / "report.json").read_text())
    checks = []
    for episode in report["episodes"]:
        public_path = CURRENT_EVIDENCE / episode["public_path"]
        private = json.loads((CURRENT_EVIDENCE / episode["private_path"]).read_text())
        visible = json.loads(public_path.read_text())
        checks.append(
            {
                "direction": episode["expansion_direction"],
                "private_parameter": private["parameters"]["expansion_direction"],
                "public_id_matches_report": public_path.name
                == f"challenge-{episode['public_id']}.json",
                "query_answers_hidden": all(
                    set(pair) == {"input"} for pair in visible["test"]
                ),
                "train_outputs_present": all(
                    set(pair) == {"input", "output"} for pair in visible["train"]
                ),
            }
        )
    booleans = [
        value
        for row in checks
        for value in row.values()
        if isinstance(value, bool)
    ]
    result = {
        "schema": "arcpuzzles-public-export-reconciliation-check-v1",
        "task_id": TASK,
        "baseline_prototype_sha256": sha256(BASELINE_PROTOTYPE),
        "current_prototype_sha256": sha256(CURRENT_PROTOTYPE),
        "baseline_public_files": baseline_rows,
        "current_public_files": current_rows,
        "public_bytes_identical": baseline_rows == current_rows,
        "current_public_names_lexically_sorted": [row["name"] for row in current_rows]
        == sorted(row["name"] for row in current_rows),
        "current_report_episode_ids": [
            row["public_id"] for row in report["episodes"]
        ],
        "checks": checks,
    }
    result["status"] = (
        "pass"
        if result["public_bytes_identical"]
        and result["current_public_names_lexically_sorted"]
        and all(booleans)
        else "fail"
    )
    out = HERE / "public-export-comparison.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
