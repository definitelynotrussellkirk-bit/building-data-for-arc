#!/usr/bin/env python3
"""Compact final consistency check for review-e0dbd5b3721b1ec3."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = "d89b3f447c00"
GEN_SHA = "a94e1ae857063d08e63cf6acb23f54bd3d171207af7c3369f9e580100f06423e"
TEST_SHA = "35b0ca3675626f89626fee84877857d75f9bb73b0d7e29426780db39f5010c8e"
PATCH_SHA = "ae21f3378072a4368814f9e97a553cd5634bed80836bc9ba7fcc16863174f225"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(rel: str):
    return json.loads((ROOT / rel).read_text())


checks: list[dict[str, object]] = []

def require(name: str, condition: bool, detail: object) -> None:
    checks.append({"name": name, "passed": bool(condition), "detail": detail})
    if not condition:
        raise AssertionError(f"{name}: {detail}")


gen = ROOT / f"repo/generators/{TASK}/generator.py"
test = ROOT / f"repo/generators/{TASK}/tests/test_generator.py"
patch = ROOT / "checks/patch-replay/source.patch"
require("generator hash", sha(gen) == GEN_SHA, sha(gen))
require("test hash", sha(test) == TEST_SHA, sha(test))
require("replayed patch hash", sha(patch) == PATCH_SHA, sha(patch))

for rel, seconds in [
    ("checks/task-tests-green-3/result.json", "3.50s authoring copy"),
    ("checks/patch-replay/fresh-task-tests/result.json", "1.75s clean replay"),
]:
    result = load(rel)
    stdout = result.get("stdout", "")
    require(f"36 tests pass: {rel}", result.get("exit_code") == 0 and "36 passed" in stdout, seconds)
    files = result["runtime_manifest"]["files"]
    gen_hashes = {row["sha256"] for row in files if row.get("library_path", "").endswith(f"{TASK}/generator.py")}
    test_hashes = {row["sha256"] for row in files if row.get("library_path", "").endswith(f"{TASK}/tests/test_generator.py")}
    require(f"runtime generator bound: {rel}", gen_hashes == {GEN_SHA}, sorted(gen_hashes))
    require(f"runtime tests bound: {rel}", test_hashes == {TEST_SHA}, sorted(test_hashes))

battery = load(f"checks/after-battery-final/checks/{TASK}_after_battery_summary.json")
require("battery all green", battery["verdict"] == "all_green" and battery["counts"] == {
    "total": 12, "green": 12, "advisory": 0, "failed": 0,
    "interrupted": 0, "pending": 0, "running": 0,
}, battery["verdict_note"])
require("battery source bound", battery["generator_file_sha256"] == GEN_SHA, battery["generator_file_sha256"])

profile = load(f"checks/after-battery-final/checks/{TASK}_after_profile_floor.json")["audits"][0]
require("profile floor", profile["status"] == "PASS" and profile["exact_hits"] == 24 and profile["draws_total"] == 60,
        {"exact_hits": profile["exact_hits"], "draws": profile["draws_total"], "per_band": profile["per_band"]})

semantic = load(f"checks/after-battery-final/checks/{TASK}_after_semantic_gate.json")["audits"][0]
lessons = semantic["lessons"]
require("semantic draws", semantic["status"] == "PASS" and semantic["strict_draws"] == 600 and semantic["census"]["crashes"] == 0,
        {"status": semantic["status"], "draws": semantic["strict_draws"], "crashes": semantic["census"]["crashes"]})
# The exact field names are retained in the report; use the public totals rather than assumptions.
prod_ok = lessons.get("materialized", lessons.get("checked", 0))
prod_bad = lessons.get("ambiguous", lessons.get("failures", 0))
rot = lessons.get("rotations", {})
rot_bad = rot.get("ambiguous", rot.get("failures", 0)) if isinstance(rot, dict) else 0
require("semantic lesson status", not semantic["errors"] and not semantic["warnings"],
        {"materialized_or_checked": prod_ok, "ambiguous_or_failures": prod_bad, "rotation_bad": rot_bad})

census = load("checks/lesson-census-final.summary.json")
summary = census["summary"]
require("large census", census["status"] == "no_ambiguity_found" and summary == {
    "requested": 300,
    "materialized": 300,
    "materialization_errors": 0,
    "pairs": 1500,
    "ambiguous": 0,
    "hook_warnings": 0,
    "scoring_errors": 0,
    "rotations": 1500,
    "ambiguous_rotations": 0,
    "rotation_hook_warnings": 0,
    "rotation_scoring_errors": 0,
    "unique_inputs": 1500,
}, summary)
require("census source bound", census["source_binding"]["generator_sha256"] == GEN_SHA,
        census["source_binding"]["generator_sha256"])
compression = load("checks/lesson-census-final.compression.json")
compressed = ROOT / compression["compressed_path"]
require("compressed census hash", sha(compressed) == compression["compressed_sha256"], sha(compressed))
raw = gzip.decompress(compressed.read_bytes())
require("restored census hash", hashlib.sha256(raw).hexdigest() == compression["original_sha256"],
        {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
require("restored census size", len(raw) == compression["original_bytes"], len(raw))

solve = load("solve/summary.json")
solve_report = load("solve/attempts/0001/report.json")
require("final solve source bound", solve["status"] == "finished" and solve["generator_hash"] == GEN_SHA,
        {"status": solve["status"], "generator_hash": solve["generator_hash"]})
require("final solve visible examples", solve_report["visible_passed"] == solve_report["visible_total"] == 4,
        {"passed": solve_report["visible_passed"], "total": solve_report["visible_total"]})
require("final solve disclosures", solve["earlier_rule_exposure"] == "yes" and solve["reference_consulted_during_solve"] is False,
        {"exposure": solve["earlier_rule_exposure"], "reference": solve["reference_consulted_during_solve"]})
blind = load("solve-blind/summary.json")
blind_report = load("solve-blind/attempts/0002/report.json")
require("blind solve complete", blind["status"] == "finished" and blind["earlier_rule_exposure"] == "no" and blind_report["visible_passed"] == 4,
        {"status": blind["status"], "attempts": blind["attempt_count"], "visible": blind_report["visible_passed"]})

review_lines = (ROOT / "REVIEW.md").read_text().splitlines()
require("maintainer brief", 8 <= 12 <= len(review_lines) and review_lines[11] == "Acceptance: routine.", review_lines[:12])
audit = (ROOT / "AUDIT.md").read_text()
require("audit headings", audit.count("## 4e53f3cd64e8") == 1 and audit.count("## 19c55a8731b1") == 1,
        [line for line in audit.splitlines() if line.startswith("## ")])
feedback = (ROOT / "FEEDBACK_TO_CODEX.md").read_text()
require("feedback ids", feedback.count("F1:") == 1 and feedback.count("F2:") == 1, ["F1", "F2"])
results = load("RESULTS.json")
require("results completion", results["completion_state"] == "complete" and results["remaining_failures"] == [],
        {"completion_state": results["completion_state"], "remaining_failures": results["remaining_failures"]})
missing = [path for cmd in results["verification_commands"] for path in cmd["evidence_paths"] if not (ROOT / path).is_file()]
require("all RESULTS evidence retained", not missing, missing)

report = {
    "schema": "review-final-verification-v1",
    "assignment_id": "review-e0dbd5b3721b1ec3",
    "task_id": TASK,
    "status": "PASS",
    "checks": checks,
}
print(json.dumps(report, indent=2, sort_keys=True))
