from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arcpuzzles.parametric_worker import evaluate_contract

ROOT = Path.cwd().resolve()
TASK = "0be8ff9b4144"
CONTRACT_PATH = ROOT / "generators" / TASK / "workspace" / "parametric" / "promotion.json"
contract = json.loads(CONTRACT_PATH.read_text())
settings = [
    {"intersection_policy": "all"},
    {"intersection_policy": "same_parity"},
    {"intersection_policy": "opposite_parity"},
]
jobs = [
    {"seed": seed, "settings": setting, "demos": 2, "queries": 4}
    for setting in settings
    for seed in (0, 17)
]
result = evaluate_contract(ROOT, TASK, contract, jobs)
full_path = ROOT.parent / "checks" / TASK / "authoring" / "worker_execution.json"
full_path.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
summary = {
    "schema": "header-intersection-policy-authoring-probe-v1",
    "task_id": TASK,
    "status": "passed",
    "jobs": jobs,
    "racket": result["racket"],
    "racket_evaluations": result["racket_evaluations"],
    "checks": result["checks"],
    "program_sha256": sorted({episode["program_sha256"] for episode in result["episodes"]}),
    "episode_output_sha256": [
        {
            "seed": episode["seed"],
            "settings": episode["settings"],
            "train": [hashlib.sha256(json.dumps(pair["output"], separators=(",", ":")).encode()).hexdigest() for pair in episode["train"]],
            "test": [hashlib.sha256(json.dumps(pair["output"], separators=(",", ":")).encode()).hexdigest() for pair in episode["test"]],
        }
        for episode in result["episodes"]
    ],
    "full_execution_sha256": hashlib.sha256(full_path.read_bytes()).hexdigest(),
    "limits": "Three declared settings, seeds 0 and 17, two demonstrations and four queries; finite evidence only.",
}
summary_path = ROOT / "generators" / TASK / "workspace" / "parametric" / "evidence" / "current" / "authoring_probe.json"
summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": "passed", "summary": str(summary_path.relative_to(ROOT)), "full": str(full_path.relative_to(ROOT.parent)), "evaluations": result["racket_evaluations"]}, sort_keys=True))
