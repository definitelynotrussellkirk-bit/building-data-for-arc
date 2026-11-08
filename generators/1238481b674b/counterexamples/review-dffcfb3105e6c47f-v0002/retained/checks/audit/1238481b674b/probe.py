from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path.cwd()
GEN_PATH = ROOT / "generators/1238481b674b/generator.py"
spec = importlib.util.spec_from_file_location("audit_1238481b674b", GEN_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

row = None
for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text(encoding="utf-8").splitlines():
    item = json.loads(line)
    if item.get("task_id") == mod.TASK_ID:
        row = item
        break
assert row is not None
pairs = [*row.get("train", []), *row.get("test", [])]
fit_matrix = {
    name: [shortcut(pair["input"]) == pair["output"] for pair in pairs]
    for name, shortcut in mod.CANONICAL_SHORTCUTS.items()
}

# A compact current-source behavioral sample, separate from the retained prior audit.
bands = {}
for band_index, band in enumerate(("easy", "medium", "hard")):
    invalid = []
    profiles = set()
    for i in range(40):
        seed = 20261012 + 1000 * band_index + i
        grid = mod.generate(seed, i, difficulty=band)
        errors = mod.self_check(grid)
        if errors:
            invalid.append({"seed": seed, "sample_index": i, "errors": errors})
        profiles.add(mod.schedule_profile(seed, i, band))
    bands[band] = {
        "draws": 40,
        "self_check_failures": invalid,
        "schedule_profiles": sorted(profiles),
    }

result = {
    "schema": "arc-audit-probe-v1",
    "task_id": mod.TASK_ID,
    "generator_version": mod.VERSION,
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "rule_hash_declared": mod.RULE_HASH,
    "canonical_pairs": len(pairs),
    "canonical_shortcuts_fit_each_pair": fit_matrix,
    "sample": bands,
    "prior_audit_used_as_lead": "review-cea4804a0e6548b7:v0001",
    "command": [
        "python3",
        "run_with_racket.py",
        "python3",
        "../checks/audit/1238481b674b/probe.py",
    ],
    "effective_cwd": str(ROOT),
}
out = ROOT.parent / "checks/audit/1238481b674b/probe.json"
out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
