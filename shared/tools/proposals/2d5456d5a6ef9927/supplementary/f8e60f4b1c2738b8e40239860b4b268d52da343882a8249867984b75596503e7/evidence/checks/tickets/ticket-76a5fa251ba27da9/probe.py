#!/usr/bin/env python3
"""Bounded, source-bound allocation-quality sample for ticket-76a5fa251ba27da9."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import re

TICKET_ID = "ticket-76a5fa251ba27da9"
TASK_ID = "e0ef0cfeaf88"
PINNED_GENERATOR_SHA256 = "e5d0042f44b1e78cdd220e54a5a8e6f8c574354631a5fade75ad6de57a4f2790"
PROBE_SEED = "b5db858602cb1869dbdbd82b99a399336c810d96a3de891ba7fdeab3c29f5e58"
EXPECTED_SAMPLE = ["3f26d45b9f51", "61c0bcd32328", "297c05190f7c"]
ROOT = Path.cwd()
WORK = ROOT.parent
OUT = WORK / "checks" / "tickets" / TICKET_ID


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_catalog() -> dict[str, dict]:
    rows = {}
    for line in (ROOT / "catalog" / "puzzles.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        rows[row["id"]] = row
    return rows


def read_test_text(task_id: str) -> str:
    paths = sorted((ROOT / "generators" / task_id / "tests").glob("*.py"))
    return "\n".join(path.read_text(encoding="utf-8") for path in paths)


def evidence_flags(task_id: str) -> dict:
    home = ROOT / "generators" / task_id
    tests = read_test_text(task_id)
    notes = (home / "notes.md").read_text(encoding="utf-8") if (home / "notes.md").exists() else ""
    shortcut = (home / "counterexamples" / "current-shortcut.json")
    all_text = tests + "\n" + notes + (shortcut.read_text(encoding="utf-8") if shortcut.exists() else "")
    test_paths = sorted(str(path.relative_to(ROOT)) for path in (home / "tests").glob("*.py"))
    parametric_manifest = home / "workspace" / "parametric" / "evidence" / "manifest.json"
    return {
        "test_files": test_paths,
        "test_function_count": len(re.findall(r"^def test_", tests, flags=re.MULTILINE)),
        "has_current_shortcut_record": shortcut.is_file(),
        "mentions_lesson_identifiable": "lesson_identifiable" in all_text,
        "mentions_three_demo_window": bool(re.search(r"three[-_ ](?:demo|example)|3[-_ ](?:demo|example)|three[-_ ]round", all_text, re.I)),
        "mentions_query_rotation_or_holdout": bool(re.search(r"rotation|holdout|every.*query", all_text, re.I | re.S)),
        "mentions_racket": "racket" in all_text.lower(),
        "mentions_rival_or_shortcut": bool(re.search(r"rival|shortcut|counterexample", all_text, re.I)),
        "has_parametric_evidence_manifest": parametric_manifest.is_file(),
        "has_four_query_prototype": bool(re.search(r"four[-_ ]query|4[-_ ]query|query_count.?=.?4", all_text, re.I)),
    }


def audit_summary(task_id: str) -> dict:
    path = ROOT / "generators" / task_id / "evidence" / "review_index.json"
    if not path.exists():
        return {"audit_count": 0, "unresolved_count": 0, "resolutions": []}
    value = json.loads(path.read_text(encoding="utf-8"))
    resolutions = [row.get("resolution") for row in value.get("audits", [])]
    unresolved = [item for item in resolutions if item not in {"resolved", "no_issue"}]
    return {"audit_count": len(resolutions), "unresolved_count": len(unresolved), "resolutions": resolutions}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((WORK / "PACKET-MANIFEST.json").read_text(encoding="utf-8"))
    catalog = read_catalog()
    pinned_path = ROOT / "generators" / TASK_ID / "generator.py"
    pinned_actual = sha(pinned_path)
    if pinned_actual != PINNED_GENERATOR_SHA256:
        raise SystemExit(f"pinned source changed: {pinned_actual}")

    sample = random.Random(int(PROBE_SEED, 16)).sample(sorted(manifest["all_ids"]), 3)
    if sample != EXPECTED_SAMPLE:
        raise SystemExit(f"sample drifted: {sample}")

    selection = manifest["selection"]
    reason_counts = Counter(reason for reasons in selection["reasons"].values() for reason in reasons)
    all_catalog_weights = Counter(catalog[task_id].get("mix_weight") for task_id in manifest["all_ids"])
    records = []
    for task_id in sample:
        row = catalog[task_id]
        source = ROOT / row["generator"]
        actual_sha = sha(source)
        packet_row = manifest["generators"][task_id]
        if actual_sha != packet_row["generator_sha256"] or actual_sha != row["reviewed_generator_sha256"]:
            raise SystemExit(f"source identity mismatch: {task_id}")
        records.append({
            "task_id": task_id,
            "generator_sha256": actual_sha,
            "rule_hash": row["reviewed_rule_hash"],
            "selection_reasons": selection["reasons"].get(task_id, []),
            "in_main_ids": task_id in manifest["main_ids"],
            "in_normal_main_pool": task_id in manifest["main_draw_policy"]["normal_ids"],
            "catalog": {
                "approved": packet_row["approved"],
                "mix_weight": row.get("mix_weight"),
                "review_status": row.get("review_status"),
                "train_safety": row.get("train_safety"),
                "sources": row.get("sources", []),
                "version": row.get("version"),
            },
            "audits": audit_summary(task_id),
            "teaching_evidence": evidence_flags(task_id),
        })

    training_context_sha = sha(WORK / "TRAINING-CONTEXT.md")
    result = {
        "schema": "arcpuzzles-allocation-quality-probe-v1",
        "ticket_id": TICKET_ID,
        "consumer": "bounded_owner_allocation_experiment_proposal",
        "probe_seed": PROBE_SEED,
        "source_binding": {
            "task_id": TASK_ID,
            "path": f"generators/{TASK_ID}/generator.py",
            "expected_sha256": PINNED_GENERATOR_SHA256,
            "actual_sha256": pinned_actual,
            "matches": True,
        },
        "dated_context": {
            "path": "TRAINING-CONTEXT.md",
            "sha256": training_context_sha,
            "status": "read_as_dated_snapshot_not_current_policy_truth",
        },
        "packet_allocation": {
            "owner_generator_count": selection["owner_generator_count"],
            "target_size": selection["target_size"],
            "quotas": selection["quotas"],
            "reason_counts": dict(sorted(reason_counts.items())),
            "main_id_count": len(manifest["main_ids"]),
            "normal_main_pool_count": len(manifest["main_draw_policy"]["normal_ids"]),
            "catalog_mix_weight_counts": {str(key): value for key, value in sorted(all_catalog_weights.items(), key=lambda x: str(x[0]))},
            "interpretation": "catalog dataset mix_weight is uniform in this packet and is distinct from authoring draw quotas/reasons",
        },
        "sample_method": "random.Random(int(ticket_seed,16)).sample(sorted(PACKET-MANIFEST.all_ids), 3)",
        "sample": records,
        "observations": [
            "3f26d45b9f51 and 297c05190f7c retain explicit rival/shortcut and multi-example teaching evidence, but neither has a retained parametric four-query evidence manifest.",
            "61c0bcd32328 has two current unresolved/needs-triage audits and no retained parametric/four-query evidence; allocating authoring work before cheap triage risks spending on a known unresolved teaching boundary.",
            "All three sampled catalog rows have mix_weight 1.0, so catalog weights alone do not express their observed differences in teachability or review burden.",
            "No sampled record is sourced from ARC-GEN or RE-ARC, so this probe cannot compare their source-specific linter, rejection, repair, ambiguity, or grammar evidence.",
        ],
        "estimated_alternative": {
            "label": "estimate_only_not_policy_change",
            "design": "Run a 30-assignment randomized comparison inside the existing unfinished-original and coverage quotas: 15 current-policy assignments versus 15 quality-gated assignments. The gate requires exact source binding and either retained lesson/rival evidence or a cheap unresolved-audit triage; it does not use high loss as a defect signal.",
            "quality_gate_arm": {
                "priority": [
                    "source-bound semantic/rival evidence with a missing four-query/parameter package",
                    "unresolved originals only after a bounded triage; replace still-unresolved candidates with the next record from the same representation stratum",
                ],
                "representation_constraint": "preserve the current unfinished-original versus coverage stratum counts within the 15 assignments",
            },
            "primary_metric": "fraction yielding a source-bound, Racket-labelled episode with at least four distinct queries identifiable from demonstrations against declared rivals",
            "cost_metrics": ["authoring minutes", "Racket invocations", "deduplication rejection rate", "maintainer triage minutes"],
            "secondary_metrics": ["parameter/four-query package completion", "unresolved-audit rate after assignment", "source-stratum representation"],
            "stopping_rule": "Stop after 30 assignments, or early when the Wilson 95% interval for the primary-rate difference excludes zero by at least 15 percentage points. Stop for harm if the gated arm lowers any protected source-stratum share by more than 10 percentage points or raises median authoring minutes by more than 25%.",
            "estimated_direction": "The gate should improve usable four-query evidence per review minute for this sampled mix, but effect size is unknown and must be measured.",
        },
        "coverage_gaps": [
            "three records are insufficient to estimate population rates",
            "no ARC-GEN or RE-ARC record was drawn",
            "no new generation, Racket execution, model-loss analysis, or deduplication run was performed",
            "source provenance was recorded but not treated as a quality guarantee",
            "proposed prototypes were not counted as production capability",
        ],
        "status": "completed",
    }
    (OUT / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Allocation-quality bounded proposal",
        "",
        f"Ticket `{TICKET_ID}`; pinned source `{TASK_ID}` matched `{PINNED_GENERATOR_SHA256}`.",
        "",
        "The ticket-seeded sample is `3f26d45b9f51`, `61c0bcd32328`, and `297c05190f7c`. "
        "The two source-bound repaired records have strong rival/lesson evidence but no retained parameter/four-query package; "
        "the unfinished original has two unresolved audits and weak retained teaching instrumentation. All three catalog mix weights are 1.0.",
        "",
        "## Proposed bounded test",
        "",
        "Randomize 30 assignments within the existing unfinished-original and coverage strata: 15 current-policy, 15 quality-gated. "
        "The gate prioritizes source-bound semantic/rival evidence missing a four-query package and requires bounded triage before assigning unresolved originals. "
        "Measure successful source-bound four-query/Racket episodes per authoring and triage minute; preserve source-stratum counts.",
        "",
        "Stop after 30, or early when a Wilson 95% interval shows at least a 15-point primary-rate difference. "
        "Stop for representation/cost harm at >10-point stratum loss or >25% median authoring-time increase.",
        "",
        "This is an estimate-only experiment proposal, not a policy change. The sample contains no ARC-GEN or RE-ARC record, so source-specific comparison is unknown.",
    ]
    (OUT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"ticket_id": TICKET_ID, "status": "completed", "sample": sample, "output": str(OUT / "result.json")}, sort_keys=True))


if __name__ == "__main__":
    main()
