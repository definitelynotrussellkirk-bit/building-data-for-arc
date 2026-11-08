#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "repo"
TASK = "90082143f2ec"

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

checks = {}
generator = REPO / "generators" / TASK / "generator.py"
prototype = REPO / "generators" / TASK / "workspace" / "parametric" / "prototype.py"
readme = prototype.with_name("README.md")
tests = REPO / "generators" / TASK / "tests" / "test_parametric_outlier_action.py"
notes = REPO / "generators" / TASK / "notes.md"
checks["generator_hash_unchanged"] = sha(generator) == "161d76e8534f32a379e801cd6cfd42462dcd40354f4a9dab2d3b04884993ef91"
checks["required_source_files_exist"] = all(p.is_file() for p in (prototype, readme, tests, notes))
checks["no_symlinks_in_changed_scope"] = not any(
    p.is_symlink() for p in (prototype, readme, tests, notes)
)
checks["prototype_marked_unapproved"] = "proposed_unapproved" in prototype.read_text() and "unapproved" in readme.read_text().lower()
checks["readme_has_exact_four_query_command"] = "--demo-count 3 --query-count 4" in readme.read_text()
final = json.loads((ROOT / "checks" / "90082143f2ec-task-tests-final" / "result.json").read_text())
checks["final_task_tests_14_of_14"] = final["passed"] and final["test_counts"] == {
    "tests": 14, "failed": 0, "errors": 0, "skipped": 0, "passed": 14
}
manifest_path = ROOT / "checks" / "parametric" / "90082143f2ec-outlier-action-v1" / "manifest.json"
manifest = json.loads(manifest_path.read_text())
checks["manifest_proposed_and_canonical_default"] = (
    manifest["status"] == "proposed_unapproved"
    and manifest["canonical_default_unchanged"] is True
    and manifest["demo_count"] == 3
    and manifest["query_count"] == 4
    and len(manifest["episodes"]) == 2
)
checks["exact_restore_program_hash"] = manifest["programs"]["restore_mode"]["sha256"] == "fce27c64e390c476ffe769e59766ad1fd179890f28233bf99a5c8176623b83e5"
public = sorted((manifest_path.parent / "public").glob("*.json"))
forbidden = (b"outlier_action", b"restore_mode", b"mask_zero", b"query_answers", b'"seed"', b"program_sha256")
checks["two_public_files_visible_only"] = len(public) == 2 and all(not any(token in p.read_bytes() for token in forbidden) for p in public)
adversarial = json.loads((ROOT / "checks" / "parametric" / "90082143f2ec-adversarial-result.json").read_text())
checks["adversarial_boundary_passed"] = adversarial["passed"] is True and adversarial["surfaces"]["sampler_and_racket_boundary"]["distinct_inputs"] == 16
results = json.loads((ROOT / "RESULTS.json").read_text())
checks["exactly_two_ticket_rows"] = len(results["supplementary_tickets"]) == 2
checks["ticket_rows_completed"] = all(row["status"] == "completed" for row in results["supplementary_tickets"])
checks["no_remaining_failures"] = results["remaining_failures"] == []
for row in results["supplementary_tickets"]:
    for evidence in row["evidence_paths"]:
        assert (ROOT / evidence).is_file(), evidence
checks["ticket_evidence_paths_exist"] = True
checks["results_complete"] = results["completion_state"] == "complete"

report = {
    "schema": "90082143f2ec-final-self-review-v1",
    "passed": all(checks.values()),
    "checks": checks,
    "declined_to_judge": [
        "Production model learnability: outside the prototype's bounded source/Racket evidence.",
        "Uniqueness against arbitrary programs: only the declared alternate setting is tested.",
        "Production parametric admission: requires separate owner qualification and approval."
    ],
    "assessment": "ready_for_packet_packaging" if all(checks.values()) else "fix_required",
}
assert report["passed"], report
out = ROOT / "checks" / "final-self-review.json"
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, indent=2, sort_keys=True))
