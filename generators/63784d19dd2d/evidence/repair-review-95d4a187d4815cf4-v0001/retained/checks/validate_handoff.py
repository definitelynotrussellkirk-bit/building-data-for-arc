#!/usr/bin/env python3
"""Cross-artifact validator for this reviewer return."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

WORK = Path(__file__).resolve().parents[1]
REPO = WORK / "repo"
MAIN = "63784d19dd2d"
PEERS = ("483682b75e12", "5de3293e1bda")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(rel: str):
    return json.loads((WORK / rel).read_text())


checks: list[dict] = []


def require(name: str, condition: bool, detail=None) -> None:
    checks.append({"name": name, "passed": bool(condition), "detail": detail})
    if not condition:
        raise AssertionError(f"{name}: {detail}")


assignment = load("ASSIGNMENT.json")
require("assignment identity", assignment["assignment_id"] == "review-95d4a187d4815cf4")
require("main source unchanged", sha(REPO / f"generators/{MAIN}/generator.py") == assignment["baseline_sha256"][f"repo/generators/{MAIN}/generator.py"])
for peer in PEERS:
    require(
        f"peer {peer} source unchanged",
        sha(REPO / f"generators/{peer}/generator.py") == assignment["baseline_sha256"][f"repo/generators/{peer}/generator.py"],
    )

manifest = load(f"repo/generators/{MAIN}/workspace/parametric/evidence/manifest.json")
for row in manifest["files"]:
    path = REPO / row["path"]
    require(f"manifest file {row['path']}", path.is_file() and sha(path) == row["sha256"])
require("manifest canonical program", manifest["canonical_program_sha256"] == sha(REPO / f"generators/{MAIN}/workspace/parametric/canonical.rkt"))
require("manifest generator", manifest["generator_sha256"] == sha(REPO / f"generators/{MAIN}/generator.py"))

qual = load(f"checks/{MAIN}/qualification/qualification.json")
execution_path = WORK / f"checks/{MAIN}/qualification/execution.json"
require("qualification status", qual["status"] == "qualified")
require("qualification execution hash", qual["execution"]["sha256"] == sha(execution_path))
require("qualification canonical hash", qual["programs"]['{"overlap_mode":"transform_only"}'] == sha(REPO / f"generators/{MAIN}/workspace/parametric/canonical.rkt"))
require("qualification alternate hash", qual["programs"]['{"overlap_mode":"mark_b_overlap"}'] == sha(REPO / f"generators/{MAIN}/workspace/parametric/mark_b_overlap.rkt"))
require("qualification jobs", len(qual["jobs"]) == 4 and {job["queries"] for job in qual["jobs"]} == {4})
execution = json.loads(execution_path.read_text())
require("qualification Racket count", execution["racket_evaluations"] == 40)
require("qualification protected Racket", execution["racket"]["protected"] is True)

self_audit = load(f"checks/{MAIN}/self-audit.json")
require("teaching audit status", self_audit["status"] == "passed" and self_audit["failures"] == [])
require("teaching audit scope", self_audit["totals"]["episodes"] == 36 and self_audit["totals"]["racket_evaluations"] == 108)
stress = load(f"checks/{MAIN}/stress-32-seeds.json")
require("stress status", stress["status"] == "passed" and stress["failures"] == [])
require("stress scope", stress["totals"]["episodes"] == 384 and stress["totals"]["labeled_pairs"] == 2368)

witness = load(f"checks/{MAIN}/causal/witness.json")
replay = load(f"checks/{MAIN}/causal/replay-final.json")
require("witness task", witness["source_binding"]["task_id"] == MAIN)
require("witness changed cells", witness["cases"][0]["intermediate_value"]["changed_output_cells"] == 22)
require("witness replay", replay["status"] == "reviewer_replayed" and replay["witness_sha256"] == sha(WORK / f"checks/{MAIN}/causal/witness.json"))
require("witness owner pending", replay["owner_acceptance"] == "not_performed" and replay["training_admitted"] is False)

final_tests = load(f"checks/{MAIN}-final-tests/result.json")
require("final task tests", final_tests["passed"] is True and final_tests["test_counts"]["passed"] == 35)

for peer, rival_count in (("483682b75e12", 7), ("5de3293e1bda", 9)):
    report = load(f"checks/{peer}/shortcut-probe.json")
    require(f"peer {peer} probe status", report["status"] == "passed" and report["unseparated_rivals"] == [])
    require(f"peer {peer} probe source", report["source_sha256"] == assignment["baseline_sha256"][f"repo/generators/{peer}/generator.py"])
    require(f"peer {peer} rival count", len(report["rivals"]) == rival_count and report["scope"]["cases_examined"] == 396)

results = load("RESULTS.json")
require("results completion", results["completion_state"] == "complete")
require("results target order", [row["task_id"] for row in results["repair_targets"]] == [MAIN, *PEERS])
require("main ready", results["repair_targets"][0]["parametric_work"]["status"] == "ready")
require("training not admitted", qual["training_admitted"] is False and self_audit["training_admitted"] is False and stress["training_admitted"] is False)

report = {
    "schema": "arcpuzzles-review-handoff-validation-v1",
    "status": "passed",
    "task_id": MAIN,
    "checks_passed": len(checks),
    "checks": checks,
    "limits": "Cross-artifact consistency only; owner integration, acceptance and training admission remain pending.",
}
out = WORK / f"checks/{MAIN}/handoff-validation.json"
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": report["status"], "checks_passed": len(checks), "out": str(out.relative_to(WORK))}))
