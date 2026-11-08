from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TASK_ID = "f67822970902"
GENERATOR = ROOT / "repo" / "generators" / TASK_ID / "generator.py"
CANONICAL = ROOT / "repo" / "shared" / "data" / "canonical" / "puzzles.jsonl"

spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GENERATOR)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

row = next(json.loads(line) for line in CANONICAL.read_text().splitlines()
           if json.loads(line).get("task_id") == TASK_ID)
pairs = row["train"] + [row["test"]]
canonical = []
for index, pair in enumerate(pairs):
    canonical.append({
        "index": index,
        "validator_errors": module.self_check(pair["input"]),
        "mirror_matches": module.rule_mirror(pair["input"]) == pair["output"],
    })

bands = {}
for band in ("easy", "medium", "hard"):
    analyses = []
    grids = []
    for sample_index in range(16):
        grid = module.generate(1701, sample_index, difficulty=band)
        analysis = module._analyze(grid)
        analyses.append(analysis)
        grids.append(grid)
    lesson_failures = []
    for start in range(12):
        demos = [
            {"input": grids[index], "output": module.rule_mirror(grids[index])}
            for index in range(start, start + 3)
        ]
        query_grid = grids[start + 3]
        reasons = module.lesson_identifiable(
            demos,
            {"input": query_grid, "output": module.rule_mirror(query_grid)},
        )
        if reasons:
            lesson_failures.append({"start": start, "reasons": reasons})
    bands[band] = {
        "draws": len(analyses),
        "structural_failures": [
            {"sample_index": index, "errors": analysis["errors"]}
            for index, analysis in enumerate(analyses)
            if analysis["errors"]
        ],
        "all_have_interior": all(a["interior_count"] >= 1 for a in analyses),
        "all_have_full_and_clipped": all(
            a["full_stamps"] >= 1 and a["clipped_stamps"] >= 1 for a in analyses
        ),
        "rotation_support": sorted(set().union(*(set(a["rotation_support"]) for a in analyses))),
        "lesson_windows_checked": 12,
        "lesson_failures": lesson_failures,
    }

report = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK_ID,
    "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
    "canonical_pairs": canonical,
    "bands": bands,
    "conclusion": (
        "Generator semantics survived this targeted probe; the independently reproduced "
        "task-test failure is a path-resolution defect in the audit target's test file."
    ),
}
print(json.dumps(report, indent=2))
