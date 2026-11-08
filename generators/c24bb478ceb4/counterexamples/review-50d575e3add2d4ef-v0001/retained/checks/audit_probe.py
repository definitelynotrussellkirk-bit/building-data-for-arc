#!/usr/bin/env python3
"""Focused findings-only probes for the two audit targets in this packet."""
from __future__ import annotations

from collections import Counter
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "repo/shared/data/canonical/puzzles.jsonl"
TARGETS = ("c24bb478ceb4", "398b42a1be77")


def load_generator(task_id: str):
    path = ROOT / "repo/generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


canonical = {}
for line in CANONICAL.read_text().splitlines():
    row = json.loads(line)
    if row.get("task_id") in TARGETS:
        canonical[row["task_id"]] = row

report = {"schema": "review-50d575e3add2d4ef-audit-probes-v1", "targets": {}}

# c24bb478ceb4: exercise canonical acceptance plus arbitrary consecutive lessons.
gen = load_generator("c24bb478ceb4")
crow = canonical[gen.TASK_ID]
canonical_errors = []
for split in ("train", "test"):
    for index, pair in enumerate(crow[split]):
        errors = gen.self_check(pair["input"])
        mirror_ok = gen.rule_mirror(pair["input"]) == pair["output"]
        if errors or not mirror_ok:
            canonical_errors.append(
                {"split": split, "index": index, "errors": errors, "mirror_ok": mirror_ok}
            )
lesson_failures = []
observed_orientations = Counter()
observed_profiles = Counter()
for difficulty in ("easy", "medium", "hard"):
    for seed in range(20):
        for start in range(8):
            demos = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(seed, sample_index, difficulty=difficulty)
                facts = gen.semantic_observables(grid)
                observed_orientations.update(facts["missing_orientations"])
                observed_profiles[(facts["height"], facts["width"], facts["n_rects"])] += 1
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            qgrid = gen.generate(seed, start + gen.EXAMPLES_NEEDED, difficulty=difficulty)
            query = {"input": qgrid, "output": gen.rule_mirror(qgrid)}
            errors = gen.lesson_identifiable(demos, query)
            if errors:
                lesson_failures.append(
                    {"difficulty": difficulty, "seed": seed, "start": start, "errors": errors}
                )
report["targets"][gen.TASK_ID] = {
    "canonical_errors": canonical_errors,
    "lesson_windows_checked": 3 * 20 * 8,
    "lesson_failures": lesson_failures,
    "observed_missing_orientations": dict(sorted(observed_orientations.items())),
    "observed_profiles": {str(key): value for key, value in sorted(observed_profiles.items())},
}

# 398b42a1be77: compare normalized prototype shape support to canonical examples.
gen = load_generator("398b42a1be77")
crow = canonical[gen.TASK_ID]

def prototype_shape(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))

canonical_shapes = []
for split in ("train", "test"):
    for index, pair in enumerate(crow[split]):
        shape = prototype_shape(pair["input"])
        canonical_shapes.append(
            {"split": split, "index": index, "size": len(shape), "shape": [list(x) for x in shape]}
        )
generated_shapes = Counter()
for difficulty in ("easy", "medium", "hard"):
    for seed in range(100):
        for sample_index in range(10):
            grid = gen.generate(seed, sample_index, difficulty=difficulty)
            shape = prototype_shape(grid)
            generated_shapes[shape] += 1
report["targets"][gen.TASK_ID] = {
    "generated_draws": sum(generated_shapes.values()),
    "generated_prototype_sizes": dict(sorted(Counter({len(shape): sum(count for s, count in generated_shapes.items() if len(s) == len(shape)) for shape in generated_shapes}).items())),
    "generated_distinct_shapes": [
        {"size": len(shape), "shape": [list(x) for x in shape], "draws": count}
        for shape, count in sorted(generated_shapes.items())
    ],
    "canonical_shapes": canonical_shapes,
    "canonical_shapes_missing_from_generated_support": [
        item for item in canonical_shapes
        if tuple(tuple(x) for x in item["shape"]) not in generated_shapes
    ],
}

out = ROOT / "checks/audit_probe.json"
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, indent=2, sort_keys=True))
