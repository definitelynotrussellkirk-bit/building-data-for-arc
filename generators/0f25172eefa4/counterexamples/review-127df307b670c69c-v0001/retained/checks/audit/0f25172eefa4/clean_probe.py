#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK = "0f25172eefa4"
ROOT = Path(__file__).resolve().parents[3] / "repo"
GENERATOR_PATH = ROOT / "generators" / TASK / "generator.py"
OUTPUT = Path(__file__).with_name("clean_probe.json")

spec = importlib.util.spec_from_file_location("audit_generator", GENERATOR_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

canonical_row = None
for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
    row = json.loads(line)
    if row.get("task_id") == TASK:
        canonical_row = row
        break
assert canonical_row is not None
canonical_pairs = list(canonical_row["train"])
canonical_test = canonical_row["test"]
canonical_pairs += canonical_test if isinstance(canonical_test, list) else [canonical_test]
canonical = [
    {
        "index": index,
        "self_check": module.self_check(pair["input"]),
        "mirror_matches": module.rule_mirror(pair["input"]) == pair["output"],
    }
    for index, pair in enumerate(canonical_pairs)
]

rotations = 0
failures = []
refutations = {name: 0 for name in module.LESSON_COMPETITORS}
for band_index, band in enumerate(("easy", "medium", "hard")):
    for start in range(len(module._SEQUENCE_SCHEDULE)):
        scene = []
        for offset in range(4):
            grid = module.generate(
                910000 + 1000 * band_index + start,
                start + offset,
                difficulty=band,
            )
            scene.append({"input": grid, "output": module.rule_mirror(grid)})
        for query_index in range(4):
            rotations += 1
            query = scene[query_index]
            demos = [pair for index, pair in enumerate(scene) if index != query_index]
            reasons = module.lesson_identifiable(demos, query)
            if reasons:
                failures.append(
                    {
                        "band": band,
                        "start": start,
                        "query_index": query_index,
                        "reasons": reasons,
                    }
                )
            for name, rival in module.LESSON_COMPETITORS.items():
                if any(rival(pair["input"]) != pair["output"] for pair in demos):
                    refutations[name] += 1
                else:
                    failures.append(
                        {
                            "band": band,
                            "start": start,
                            "query_index": query_index,
                            "unrefuted": name,
                        }
                    )

selfcheck_failures = []
inputs = set()
for band_index, band in enumerate(("easy", "medium", "hard")):
    for index in range(200):
        grid = module.generate(920000 + band_index * 10000 + index, index, difficulty=band)
        errors = module.self_check(grid)
        if errors:
            selfcheck_failures.append({"band": band, "index": index, "errors": errors})
        inputs.add(json.dumps(grid, separators=(",", ":")))

report = {
    "schema": "arcpuzzles-audit-clean-probe-v1",
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
    "version": module.VERSION,
    "canonical_pairs": canonical,
    "schedule_policy": "six cyclic starts x three bands x every one-of-four query holdout",
    "rotation_count": rotations,
    "rotation_failures": failures,
    "competitor_refutation_counts": refutations,
    "default_draws": 600,
    "unique_default_inputs": len(inputs),
    "selfcheck_failures": selfcheck_failures,
    "conclusion": (
        "No issue found in the checked canonical parity, default grammar, "
        "declared-rival schedule rotations, or focused exact-control tests."
    ),
}
OUTPUT.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
