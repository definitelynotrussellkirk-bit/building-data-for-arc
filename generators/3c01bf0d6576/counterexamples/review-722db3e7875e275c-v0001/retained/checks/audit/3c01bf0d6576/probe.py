from __future__ import annotations
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GEN_PATH = ROOT / "repo/generators/3c01bf0d6576/generator.py"
spec = importlib.util.spec_from_file_location("audit_3c01bf0d6576", GEN_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def frozen(grid):
    return tuple(tuple(row) for row in grid)

bands = ("easy", "medium", "hard")
per_band = 100
rival_names = sorted(mod.LESSON_COMPETITORS)
result = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": mod.TASK_ID,
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "declared_rule_hash": mod.RULE_HASH,
    "lesson_policy": "seed=910000+band_offset+lesson, start_sample_index=lesson*11, four consecutive demos plus one query",
    "per_band": per_band,
    "bands": {},
    "declared_rivals": rival_names,
}
parity_inputs = []
for bi, band in enumerate(bands):
    unique = set()
    transform_counts = Counter()
    texture_counts = Counter()
    unidentifiable = []
    survivor_counts = Counter()
    validation_failures = []
    for lesson in range(per_band):
        seed = 910000 + bi * 10000 + lesson
        start = lesson * 11
        pairs = []
        for offset in range(mod.EXAMPLES_NEEDED + 1):
            grid = mod.generate(seed, start + offset, difficulty=band)
            errs = mod.self_check(grid)
            if errs:
                validation_failures.append({"lesson": lesson, "offset": offset, "errors": errs})
            unique.add(frozen(grid))
            info, analyze_errors = mod._analyze(grid)
            assert not analyze_errors
            transform_counts[str(info["transform"])] += 1
            texture_counts[info["texture"]] += 1
            pairs.append({"input": grid, "output": mod._solve_python(grid)})
            if len(parity_inputs) < 64:
                parity_inputs.append(grid)
        reasons = mod.lesson_identifiable(pairs[:-1], pairs[-1])
        survivors = []
        for name, rival in mod.LESSON_COMPETITORS.items():
            if all(rival(p["input"]) == p["output"] for p in pairs[:-1]):
                survivors.append(name)
                survivor_counts[name] += 1
        if reasons or survivors:
            unidentifiable.append({
                "lesson": lesson,
                "seed": seed,
                "sample_index": start,
                "reasons": reasons,
                "survivors": sorted(survivors),
            })
    result["bands"][band] = {
        "lessons": per_band,
        "materialized_pairs": per_band * (mod.EXAMPLES_NEEDED + 1),
        "unique_inputs": len(unique),
        "validation_failures": validation_failures,
        "unidentifiable": unidentifiable,
        "declared_rival_survivor_counts": dict(survivor_counts),
        "transform_counts": dict(transform_counts),
        "texture_counts": dict(texture_counts),
    }
result["status"] = "pass" if all(
    not b["validation_failures"] and not b["unidentifiable"]
    for b in result["bands"].values()
) else "fail"
here = Path(__file__).resolve().parent
(here / "probe.json").write_text(json.dumps(result, indent=2) + "\n")
(here / "parity-input.json").write_text(json.dumps(parity_inputs, indent=2) + "\n")
print(json.dumps({
    "status": result["status"],
    "bands": {k: {"unique_inputs": v["unique_inputs"], "unidentifiable": len(v["unidentifiable"]), "validation_failures": len(v["validation_failures"])} for k,v in result["bands"].items()},
    "parity_inputs": len(parity_inputs),
}, indent=2))
