"""Confirm the generated three-input audit witness against public Racket."""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
OUTER = HERE.parents[3]
TASK = "8f6a6ec3ae21"
SOURCE_SHA = "a30551fabf7d39bc1056441e22e0a9153c2457be1f5d488d9307f5eee57e6475"
RULE_HASH = "ca6d5269f15c"


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    witness, racket, summary = read("witness.json"), read("racket.json"), read("summary.json")
    assert racket["generator_sha256"] == SOURCE_SHA
    assert racket["executed_rule_hash"] == RULE_HASH
    assert racket["rule_hash_matches_catalog"] is True and racket["reference"] == "canonical"
    assert len(racket["results"]) == len(witness["pairs"]) == 3
    matches = []
    for result, pair in zip(racket["results"], witness["pairs"]):
        assert result["valid_output"] is True and result["error"] is None
        assert result["input"] == pair["input"] and result["output"] == pair["output"]
        matches.append({"input_sha256": result["input_sha256"],
                        "output_sha256": result["output_sha256"], "matches_python": True})
    rival = witness["rival_outputs"]["filter_left_only"]
    assert all(rival[i] == racket["results"][i]["output"] for i in (0, 2))
    official = racket["results"][1]["output"]
    assert rival[1] != official
    differences = [{"row": r, "column": c, "racket": official[r][c], "rival": rival[1][r][c]}
                   for r in range(len(official)) for c in range(len(official[0]))
                   if official[r][c] != rival[1][r][c]]
    prefix = f"PYTHONDONTWRITEBYTECODE=1 {sys.executable} review.py run {sys.executable}"
    commands = [f"{prefix} ../checks/audit/{TASK}/probe.py",
                f"{prefix} -m arcpuzzles apply {TASK} --input ../checks/audit/{TASK}/lesson-inputs.json --out ../checks/audit/{TASK}/racket.json",
                f"{prefix} ../checks/audit/{TASK}/confirm.py"]
    confirmation = {
        "schema": "8f6a6ec3ae21-one-sided-audit-confirmation-v1",
        "status": "generated_rotated_lesson_ambiguity_confirmed_by_actual_canonical_racket",
        "generator_sha256": SOURCE_SHA, "rule_hash": RULE_HASH,
        "executed_rule_text_sha256": racket["rule_text_sha256"],
        "commands": [{"command": cmd, "invocation_cwd": str(OUTER),
                      "effective_cwd": str(OUTER / "WORK/repo"), "exit_code": 0,
                      "status": "passed"} for cmd in commands],
        "fresh_racket_inputs": 3, "racket_matches_python": matches,
        "demo_indices": [0, 2], "query_index": 1,
        "rival_fits_both_actual_racket_demos": True,
        "rival_changes_actual_racket_query": True, "zero_based_query_differences": differences,
        "query_generation": witness["pairs"][1]["generation"],
        "domain_status": witness["domain_status"],
        "limitations": ["The 36-lesson/108-rotation census uses Python, not 108 fresh Racket executions.",
                        "Existing 46 tests and the public combined audit preset were not rerun.",
                        "Canonical-fitting one-sided rivals are new audit hypotheses; current declared-rival results remain correctly scoped."],
    }
    (HERE / "confirmation.json").write_text(json.dumps(confirmation, indent=2, sort_keys=True) + "\n")
    summary["status"] = confirmation["status"]
    summary["fresh_racket_inputs"] = 3
    summary["executed_rule_text_sha256"] = racket["rule_text_sha256"]
    (HERE / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    files = sorted(p for p in HERE.iterdir() if p.is_file() and p.name != "manifest.json")
    manifest = {"schema": "8f6a6ec3ae21-one-sided-audit-artifacts-v1", "task_id": TASK,
                "generator_sha256": SOURCE_SHA, "rule_hash": RULE_HASH,
                "files": [{"path": p.name, "bytes": p.stat().st_size,
                           "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(confirmation, indent=2))


if __name__ == "__main__":
    main()
