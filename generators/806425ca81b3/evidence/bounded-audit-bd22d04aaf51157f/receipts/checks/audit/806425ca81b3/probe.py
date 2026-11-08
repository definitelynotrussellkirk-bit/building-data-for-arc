from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

PACKET = Path(__file__).resolve().parents[3]
REPO = PACKET / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import canonical_pairs, find_root

TASK = "806425ca81b3"
SOURCE = REPO / "generators" / TASK / "generator.py"

spec = importlib.util.spec_from_file_location("audit_806_generator", SOURCE)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def pair(grid):
    return {"input": copy.deepcopy(grid), "output": mod.rule_mirror(grid)}


results = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "rule_hash": mod.RULE_HASH,
    "checks": {},
    "failures": [],
}

canon = canonical_pairs(TASK, root=REPO)
canon_ok = True
for i, item in enumerate(canon):
    before = copy.deepcopy(item["input"])
    errors = mod.self_check(before)
    actual = mod.rule_mirror(before)
    if errors or actual != item["output"] or before != item["input"]:
        canon_ok = False
        results["failures"].append({"kind": "canonical", "index": i, "errors": errors})
results["checks"]["canonical_pairs"] = {"count": len(canon), "passed": canon_ok}

# Every named canonical shortcut must actually fit all canonical pairs.
shortcut_results = {}
for name, rival in mod.CANONICAL_SHORTCUTS.items():
    fits = [rival(item["input"]) == item["output"] for item in canon]
    shortcut_results[name] = {"fits": sum(fits), "total": len(fits), "all_fit": all(fits)}
    if not all(fits):
        results["failures"].append({"kind": "shortcut_contract", "name": name, "fits": fits})
results["checks"]["canonical_shortcuts"] = shortcut_results

# Test all legal exact-axis corner combinations in all bands.
override_cases = 0
for band in ("easy", "medium", "hard"):
    for h in (8, 14):
        for w in (9, 14):
            for active in (1, 5):
                for profile in mod.SCENE_PROFILES:
                    requested = {"grid_h": h, "grid_w": w, "active_rows": active, "scene_profile": profile}
                    grid = mod.generate(4201, 31, difficulty=band, **requested)
                    override_cases += 1
                    got = mod.observe_overrides(grid)
                    errors = mod.self_check(grid)
                    if got != requested or errors:
                        results["failures"].append({
                            "kind": "override", "band": band, "requested": requested,
                            "observed": got, "errors": errors,
                        })
results["checks"]["exact_override_corners"] = {
    "cases": override_cases,
    "passed": not any(f["kind"] == "override" for f in results["failures"]),
}

# Large deterministic schedule/window stress. Each four-demo window must kill every
# named competitor that could change the next query. Covers every cyclic phase.
lessons = 0
inputs = set()
profile_counts = {band: {p: 0 for p in mod.SCENE_PROFILES} for band in ("easy", "medium", "hard")}
for band in ("easy", "medium", "hard"):
    for seed in range(128):
        for start in range(8):
            demos = []
            for offset in range(mod.EXAMPLES_NEEDED):
                grid = mod.generate(seed, start + offset, difficulty=band)
                errors = mod.self_check(grid)
                if errors:
                    results["failures"].append({"kind": "self_check", "band": band, "seed": seed, "index": start + offset, "errors": errors})
                profile_counts[band][mod.observe_overrides(grid)["scene_profile"]] += 1
                inputs.add(json.dumps(grid, separators=(",", ":")))
                demos.append(pair(grid))
            query_grid = mod.generate(seed, start + mod.EXAMPLES_NEEDED, difficulty=band)
            inputs.add(json.dumps(query_grid, separators=(",", ":")))
            query = pair(query_grid)
            reasons = mod.lesson_identifiable(demos, query)
            lessons += 1
            if reasons:
                results["failures"].append({"kind": "lesson_identifiability", "band": band, "seed": seed, "start": start, "reasons": reasons})
results["checks"]["rolling_lessons"] = {
    "lessons": lessons,
    "unique_inputs": len(inputs),
    "cyclic_starts_per_seed": 8,
    "seed_range": [0, 127],
    "profile_counts": profile_counts,
    "passed": not any(f["kind"] in {"self_check", "lesson_identifiability"} for f in results["failures"]),
}

# All named mutation fixtures must remain rejected.
mutation = []
for name, grid in mod.mutation_fixtures():
    errors = mod.self_check(grid)
    mutation.append({"name": name, "rejected": bool(errors), "errors": errors})
    if not errors:
        results["failures"].append({"kind": "mutation_accepted", "name": name})
results["checks"]["mutation_fixtures"] = mutation

# Save a reproducible 64-grid Racket parity batch for the supported apply command.
parity_inputs = []
parity_expected = []
for sample_index in range(64):
    band = ("easy", "medium", "hard")[sample_index % 3]
    grid = mod.generate(9000 + sample_index // 8, sample_index, difficulty=band)
    parity_inputs.append(grid)
    parity_expected.append(mod.rule_mirror(grid))
(PACKET / "checks/audit/806425ca81b3/input.json").write_text(json.dumps(parity_inputs, indent=2) + "\n")
(PACKET / "checks/audit/806425ca81b3/expected-python.json").write_text(json.dumps(parity_expected, indent=2) + "\n")
results["checks"]["racket_parity_batch_prepared"] = {"count": len(parity_inputs)}

results["passed"] = not results["failures"]
Path(__file__).with_name("probe.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
print(json.dumps({"passed": results["passed"], "failures": len(results["failures"]), "lessons": lessons, "unique_inputs": len(inputs), "override_cases": override_cases}, sort_keys=True))
raise SystemExit(0 if results["passed"] else 1)
