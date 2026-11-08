from __future__ import annotations
import json
from pathlib import Path
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "5a9f7b8b0fa0"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK_ID, root=ROOT)
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)

results = {}
for name, rival in GEN.CANONICAL_SHORTCUTS.items():
    mismatches = []
    errors = []
    for pair in PAIRS:
        identity = {
            "variant": pair["variant"],
            "split": pair["split"],
            "pair_index": pair["pair_index"],
        }
        try:
            predicted = rival(pair["input"])
        except Exception as exc:  # retained as evidence, not hidden
            errors.append({"identity": identity, "error": f"{type(exc).__name__}: {exc}"})
            continue
        if predicted != pair["output"]:
            mismatches.append({
                "identity": identity,
                "expected_output": pair["output"],
                "predicted_output": predicted,
            })
    results[name] = {
        "checked": len(PAIRS),
        "matches": len(PAIRS) - len(mismatches) - len(errors),
        "mismatch_count": len(mismatches),
        "error_count": len(errors),
        "mismatches": mismatches,
        "errors": errors,
    }

report = {
    "schema": "arcpuzzles-adversarial-audit-v1",
    "task_id": TASK_ID,
    "generator_path": str(SOURCE.relative_to(ROOT)),
    "generator_sha256": SOURCE_SHA,
    "declared_rule_hash": getattr(GEN, "RULE_HASH", None),
    "canonical_labeled_pair_count": len(PAIRS),
    "finding": "CANONICAL_SHORTCUTS contains rivals that do not fit every labeled canonical pair; these are lesson competitors, not canonical shortcuts.",
    "declarations": sorted(GEN.CANONICAL_SHORTCUTS),
    "results": results,
    "actionable": any(row["mismatch_count"] or row["error_count"] for row in results.values()),
    "command": ["python3", "review.py", "run", "python3", "../checks/audit/5a9f7b8b0fa0/audit_probe.py"],
    "cwd": "packet_root",
}
(HERE / "canonical-shortcut-declarations.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({
    "task_id": TASK_ID,
    "generator_sha256": SOURCE_SHA,
    "canonical_pairs": len(PAIRS),
    "mismatch_counts": {name: row["mismatch_count"] for name, row in results.items()},
}, indent=2))
assert report["actionable"]
