from __future__ import annotations
import json
from pathlib import Path
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "aa45957d8241"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK_ID, root=ROOT)
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)

cases = []
for pair in PAIRS:
    errors = list(GEN.self_check(pair["input"]))
    cases.append({
        "identity": {
            "variant": pair["variant"],
            "split": pair["split"],
            "pair_index": pair["pair_index"],
        },
        "shape": [len(pair["input"]), len(pair["input"][0])],
        "self_check_errors": errors,
        "input": pair["input"] if errors else None,
    })
rejected = [case for case in cases if case["self_check_errors"]]
report = {
    "schema": "arcpuzzles-adversarial-audit-v1",
    "task_id": TASK_ID,
    "generator_path": str(SOURCE.relative_to(ROOT)),
    "generator_sha256": SOURCE_SHA,
    "declared_rule_hash": getattr(GEN, "RULE_HASH", None),
    "canonical_labeled_pair_count": len(PAIRS),
    "canonical_rejected_count": len(rejected),
    "finding": "self_check rejects labeled canonical inputs, so the declared generator domain does not contain the task it is supposed to model.",
    "semantic_contract_present": any(hasattr(GEN, name) for name in ("strict_canonical_like", "SEMANTIC_WITNESSES", "lesson_identifiable")),
    "cases": cases,
    "command": ["python3", "review.py", "run", "python3", "../checks/audit/aa45957d8241/audit_probe.py"],
    "cwd": "packet_root",
}
(HERE / "canonical-selfcheck.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({
    "task_id": TASK_ID,
    "generator_sha256": SOURCE_SHA,
    "canonical_pairs": len(PAIRS),
    "canonical_rejected": len(rejected),
    "semantic_contract_present": report["semantic_contract_present"],
}, indent=2))
assert rejected
