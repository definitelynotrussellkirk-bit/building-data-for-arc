from __future__ import annotations
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
WORK = next(p for p in HERE.parents if (p / "repo/generators").is_dir())
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
sys.path.insert(0, str(REPO / "shared/tools"))
TASK_ID = "4c93dc1552b3"
SOURCE = REPO / "generators" / TASK_ID / "generator.py"

spec = importlib.util.spec_from_file_location("audit_4c93", SOURCE)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
row = None
with (REPO / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
    for line in handle:
        candidate = json.loads(line)
        if candidate.get("task_id") == TASK_ID:
            row = candidate
            break
assert row is not None
pairs = []
for split in ("train", "test"):
    part = row[split]
    pairs.extend(part if isinstance(part, list) else [part])
results = {}
for name, fn in sorted(mod.CANONICAL_SHORTCUTS.items()):
    mismatches = [
        index
        for index, pair in enumerate(pairs)
        if fn(pair["input"]) != pair["output"]
    ]
    results[name] = {
        "checked": len(pairs),
        "mismatch_count": len(mismatches),
        "mismatch_pair_indices": mismatches,
        "fits_all_canonical_pairs": not mismatches,
    }
record = {
    "task_id": TASK_ID,
    "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "canonical_pair_count": len(pairs),
    "canonical_shortcut_results": results,
    "finding": "CANONICAL_SHORTCUTS aliases all SEMANTIC_RIVALS, but only canonical-fitting shortcuts belong there.",
    "full_check_log": "checks/audit/4c93dc1552b3/checks/4c93dc1552b3_audit_semantic_gate.log",
}
(HERE.parent / "reproduction.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))
