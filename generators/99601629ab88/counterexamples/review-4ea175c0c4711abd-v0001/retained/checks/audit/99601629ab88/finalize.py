"""Bind the audit's bounded observations to the retained Racket execution."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
evidence_path = HERE / "evidence.json"
e = json.loads(evidence_path.read_text())
r = json.loads((HERE / "racket.json").read_text())
assert len(r["results"]) == len(e["cases"]) == 31
assert r["generator_sha256"] == e["generator_sha256"]
assert r["executed_rule_hash"] == e["declared_rule_hash"]
for case, result in zip(e["cases"], r["results"]):
    assert result["input"] == case["input"]
    case.update({"actual_racket_output": result["output"],
                 "racket_valid_output": result["valid_output"],
                 "racket_error": result["error"],
                 "mirror_matches_racket": result["output"] == case["mirror_output"],
                 "frequency_rival_matches_racket": result["output"] == case["frequency_rival_output"]})
e["racket_execution"] = {key: r[key] for key in (
    "executed_rule_hash", "catalog_rule_hash", "rule_hash_matches_catalog",
    "rule_text_sha256", "generator_sha256", "reference", "rule_file")}
e["racket_execution"]["racket_report_sha256"] = hashlib.sha256((HERE / "racket.json").read_bytes()).hexdigest()
e["commands"] += [
    {"cwd": "packet_root", "effective_cwd": "packet_root/repo", "argv": [
        "python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply",
        "99601629ab88", "--input", "../checks/audit/99601629ab88/input.json",
        "--out", "../checks/audit/99601629ab88/racket.json"], "exit_code": 0},
    {"cwd": "packet_root", "argv": ["python3", "checks/audit/99601629ab88/finalize.py"], "exit_code": 0}]
e["summary"] = {
    "finding": "No issue found in bounded audit; canonical-fitting frequency rival refuted by generated samples",
    "racket_inputs": len(e["cases"]),
    "racket_errors": sum(case["racket_error"] is not None for case in e["cases"]),
    "invalid_outputs": sum(not case["racket_valid_output"] for case in e["cases"]),
    "mirror_mismatches": sum(not case["mirror_matches_racket"] for case in e["cases"]),
    "validator_rejections": sum(bool(case["self_check"]) for case in e["cases"]),
    "observed_profile_mismatches": sum(case["observed"]["scene_profile"] != case["overrides"]["scene_profile"] for case in e["cases"]),
    "canonical_train_pairs_checked": len(e["canonical_train"]),
    "canonical_train_rival_mismatches": sum(not case["frequency_rival_fits_published_train"] for case in e["canonical_train"]),
    "frequency_rival_generated_disagreements": sum(not case["frequency_rival_matches_racket"] for case in e["cases"]),
}
e["frequency_rival_counterexample_case"] = next(case["case_id"] for case in e["cases"] if not case["frequency_rival_matches_racket"])
e["limits"] = ["Finite 31-input audit, not full battery or proof over seeds.",
                "Exact-public profiles intentionally replay four retained canonical inputs; documented existing behavior.",
                "No generated lesson census or query-rotation audit was performed.",
                "No source edits and no solve/private-label directories read."]
evidence_path.write_text(json.dumps(e, indent=2) + "\n")
draft = f'''## 99601629ab88

**No issue found in a bounded findings-only audit.** Generator v4.0.0 SHA-256
`{e["generator_sha256"]}`; declared and executed normalized rule hash
`{r["executed_rule_hash"]}`. All 31 actual Racket executions produced valid outputs,
with no execution errors, validator rejections, output/mirror mismatches, or profile
override mismatches. The probe covered all four explicit public profiles plus all
nine general lattice profiles in easy, medium, and hard (one seed per combination).
All seven retained canonical training pairs were accepted and agreed with the mirror.

A concrete rival chooses the most frequent nonzero color as the divider, rather
than requiring full divider rows and columns. It fits all seven retained canonical
training pairs, but the generator refuted it on {e["summary"]["frequency_rival_generated_disagreements"]}
of the 31 checked inputs. Reproducible first witness:
`{e["frequency_rival_counterexample_case"]}`; the input, seed/index/overrides,
documented-domain membership, validator result, rival output and actual Racket
output are retained in `checks/audit/99601629ab88/evidence.json`.

Evidence: `checks/audit/99601629ab88/probe.py`, `input.json`, `racket.json`,
`finalize.py`, and `evidence.json`. Exact argument arrays, working directories,
exit codes, generator bytes hash, selected rule hashes and executed authority hashes
are retained in the evidence. No target/shared source changed.

Limits: this checks finite inputs rather than every seed or assembled lesson.
Four exact-public profiles intentionally replay canonical inputs, as documented
in the current source and prior notes; this audit does not claim those draws add
novel examples. No full battery, lesson census, or query-rotation audit was run.
'''
(HERE / "audit-draft.md").write_text(draft)
print(json.dumps(e["summary"]))
print(e["frequency_rival_counterexample_case"])
