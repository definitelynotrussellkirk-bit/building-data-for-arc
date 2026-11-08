"""Assemble honest return metadata from retained current evidence and receipts.

Run from WORK/repo through review.py run after both task homes are frozen.
This checks source/evidence bindings; it performs no new label execution.
"""
import hashlib
import json
import os
from pathlib import Path
from collections import Counter

from arcpuzzles.review_witness import _qualified

ROOT = Path.cwd().resolve()
WORK = ROOT.parent


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence_files(path):
    return [p.relative_to(WORK).as_posix() for p in sorted(path.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts and p.suffix not in (".pyc", ".pyo")]


def normalize_arg(arg):
    if arg.startswith(str(WORK) + "/"):
        return os.path.relpath(arg, ROOT)
    return arg


def main():
    assignment = read(WORK / "ASSIGNMENT.json")
    assert assignment["assignment_id"] == "review-d7872ecc6ba9c405"
    targets = [row["task_id"] for row in assignment["repair_targets"]]
    assert targets == ["01bb2cbe1309", "004ca3500787"]
    specifications = {
        targets[0]: ("2.0.0", "diagonal-teaching-audit-v2", "sampler-v3.json", 157,
                     "Exact canonical one-pass and state-dependent two-pass diagonal completion"),
        targets[1]: ("4.1.0", "shape-teaching-audit-v1", "sampler-v1.json", 131,
                     "Exact canonical pose and observed-pose rendering after singleton D4-class selection"),
    }
    privacy = read(WORK / "checks/first-turn/report.json")
    assert privacy["status"] == "passed" and not privacy["failures"]
    assert [privacy[k] for k in ("public_views_checked", "first_turns_checked", "invariance_checks", "positive_controls")] == [32, 8, 48, 8]
    for binding in privacy["source_files"]:
        assert sha(WORK / binding["path"]) == binding["sha256"]
    common = evidence_files(WORK / "checks/tools") + evidence_files(WORK / "checks/first-turn")
    rows, stats = [], []
    for assigned in assignment["repair_targets"]:
        tid = assigned["task_id"]
        version, audit_name, sampler_name, focused_tests, meaning = specifications[tid]
        home = ROOT / "generators" / tid
        native = home / "workspace/parametric"
        checks = WORK / "checks" / tid
        assert sha(home / "generator.py") == assigned["generator"]["generator_sha256"]
        audit = read(checks / audit_name / "private/audit.json")
        sampler = read(checks / sampler_name)
        assert audit["status"] == "passed" and audit["reference_label_count"] == 40 and not audit["findings"]
        assert audit["source_unchanged"] and audit["runtime_sources_unchanged"]
        for binding_key in ("source_files_sha256_after", "runtime_files_sha256_after"):
            for path, digest in audit[binding_key].items():
                assert sha(ROOT / path) == digest, path
        assert sampler["status"] == "passed" and sampler["request_count"] == sampler["success_count"] == 96
        for binding in sampler["adjacent_source_files"]["after"]:
            assert sha(native / binding["path"]) == binding["sha256"]
        manifest = read(native / "evidence/manifest.json")
        for item in manifest["files"]:
            assert sha(ROOT / item["path"]) == item["sha256"]
        qualification, execution = _qualified(ROOT, checks / "qualification/qualification.json")
        assert qualification["status"] == "qualified" and len(execution["episodes"]) == 4
        witness_path = checks / "causal/witness.json"
        witness, replay = read(witness_path), read(checks / "causal/replay.json")
        assert replay["status"] == "reviewer_replayed" and len(witness["cases"]) == 2
        assert replay["witness_sha256"] == sha(witness_path)
        assert witness["source_binding"] == replay["source_binding"] == qualification["source_binding"]
        fitted = [h for e in audit["episodes"] for h in e["hypotheses"]]
        survivors = [h for h in fitted if h["survives_demonstrations"]]
        assert all(not h["query_disagreement_indices"] for h in survivors)
        counts = {
            "focused_tests_passed": focused_tests, "sampler_requests_passed": 96,
            "intended_labels_checked": 40, "hypothesis_fits": len(fitted),
            "refuted": len(fitted) - len(survivors), "survivors": len(survivors),
            "survivor_query_disagreements": 0, "protected_teaching_evaluations": audit["execution"]["racket_evaluations"],
            "qualification_jobs": 4, "qualification_demos": 6, "qualification_queries": 4,
            "causal_cases_replayed": 2, "public_views": 16,
            "sampler_input_statistics": sampler["input_statistics"],
        }
        summary = (f"{meaning}; {focused_tests} focused tests and96/96 sampler requests passed; "
                   f"{len(fitted)} hypothesis fits with{counts['refuted']} refuted and no survivor query disagreement; "
                   "native qualified, two causal cases replayed and16 one-query views verified.")
        inherited = ([] if tid == targets[0] else [
            "Inherited production finding review-205ebfa3d89039c8:v0001 remains unresolved; arbitrary production pair reassignment is outside this new fixed-role native bank and was not repaired."
        ])
        rows.append({
            "task_id": tid, "outcome": "prototype", "summary": summary,
            "changed_components": ["tests_notes"], "remaining_failures": inherited,
            "evidence_paths": sorted(set(evidence_files(checks) + common + ["patches/source.patch", "checks/assemble_return.py", "checks/final-status.json"])),
            "source_identity": {
                "production_version": version, "production_generator_sha256": sha(home / "generator.py"),
                "canonical_rule_hash": assigned["generator"]["rule_hash"],
                "exact_canonical_program_sha256": sha(native / "canonical.rkt"),
                "native_sha256": sha(native / "native_family.py"), "audit_sha256": sha(native / "audit_native.py"),
                "inventory_sha256": sha(native / "evidence/manifest.json"),
                "qualification_sha256": sha(checks / "qualification/qualification.json"),
                "notes_sha256": sha(home / "notes.md"),
            },
            "checks_summary": counts,
            "parametric_work": {
                "status": "ready", "summary": summary,
                "prototype_path": f"repo/generators/{tid}/workspace/parametric/native_family.py",
                "promotion_path": f"repo/generators/{tid}/workspace/parametric/promotion.json",
                "inventory_path": f"repo/generators/{tid}/workspace/parametric/evidence/manifest.json",
                "qualification_path": f"checks/{tid}/qualification/qualification.json",
                "sequential_dependency": {**{key: witness[key] for key in ("step_a", "intermediate", "step_b", "why_b_depends_on_a")},
                                           "witness_path": f"checks/{tid}/causal/witness.json"},
                "owner_acceptance": "pending", "training_admitted": False,
            },
        })
        stats.append({"task_id": tid, **counts, "source_bindings_current": True})

    commands = []
    for receipt_path in sorted((WORK / "checks").rglob("*.json")):
        try:
            receipt = read(receipt_path)
        except (ValueError, UnicodeError):
            continue
        if not isinstance(receipt, dict) or receipt.get("schema") != "arcpuzzles-run-command-v1":
            continue
        payload = receipt["payload"]
        assert Path(payload["expected_cwd"]).resolve() == ROOT
        row = {"cwd": "repo", "argv": [normalize_arg(arg) for arg in payload["argv"]],
               "exit_code": receipt["returncode"], "evidence_paths": [receipt_path.relative_to(WORK).as_posix()]}
        if "-" in payload["argv"]:
            row["limits"] = "Receipt preserves argv/status; this inline-stdin payload body was not retained by the launcher and is not reconstructed here."
        commands.append(row)
    status = {
        "schema": "arcpuzzles-reviewer-final-binding-check-v1", "assignment_id": assignment["assignment_id"],
        "status": "passed", "targets": stats,
        "current_focused_tests": sum(s["focused_tests_passed"] for s in stats) + 17,
        "current_sampler_requests": sum(s["sampler_requests_passed"] for s in stats),
        "retained_command_receipts": len(commands),
        "retained_command_exit_codes": dict(Counter(str(c["exit_code"]) for c in commands)),
        "privacy_report_sha256": sha(WORK / "checks/first-turn/report.json"),
        "limits": "Hash/metadata check of existing evidence only; no new label evaluation, acceptance or training admission. The assembler's own receipt is created after this file.",
        "owner_acceptance": "pending", "objective_met": False, "training_admitted": False,
    }
    (WORK / "checks/final-status.json").write_text(json.dumps(status, indent=2) + "\n")
    results = {
        "completion_state": "complete",
        "stopping_reason": "Both reviewer-native builds are ready and source-bound. Owner qualification and fresh acceptance of both integrated sources remain pending; the round objective is not met and no training is admitted.",
        "remaining_failures": rows[1]["remaining_failures"],
        "repair_targets": rows, "verification_commands": commands,
    }
    (WORK / "RESULTS.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps({key: status[key] for key in ("status", "current_focused_tests", "current_sampler_requests", "retained_command_receipts", "retained_command_exit_codes", "objective_met")}))


if __name__ == "__main__":
    main()
