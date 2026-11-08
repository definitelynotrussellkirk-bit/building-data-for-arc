#!/usr/bin/env python3
"""Reproduce the homogeneous-orientation lesson shortcut on the current source."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import importlib.util

GENERATOR_PATH = Path(__file__).resolve().parents[1] / "generator.py"
spec = importlib.util.spec_from_file_location("c24bb478ceb4_generator", GENERATOR_PATH)
assert spec and spec.loader
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def first_orientation_for_all(grid):
    errors, rectangles = gen._analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    first = min(rectangles, key=lambda rect: rect["color"])
    orientation = first["missing_name"]
    out = [list(row) for row in grid]
    for rect in rectangles:
        r, c = gen._corner_map(rect["rows"], rect["cols"])[orientation]
        out[r][c] = rect["color"]
    return out


def eq(a, b):
    return [list(row) for row in a] == [list(row) for row in b]


def main():
    src = GENERATOR_PATH
    records = []
    for band in ("easy", "medium", "hard"):
        for start in range(18):
            seed = 3400 + start
            pairs = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED + 1):
                inp = gen.generate(seed, sample_index, difficulty=band)
                pairs.append({"input": inp, "output": gen.rule_mirror(inp)})
            demo_fits = all(eq(first_orientation_for_all(p["input"]), p["output"]) for p in pairs[:-1])
            query_fits = eq(first_orientation_for_all(pairs[-1]["input"]), pairs[-1]["output"])
            if demo_fits:
                records.append({
                    "band": band,
                    "seed": seed,
                    "start": start,
                    "demo_indices": list(range(start, start + gen.EXAMPLES_NEEDED)),
                    "query_index": start + gen.EXAMPLES_NEEDED,
                    "demo_patterns": [gen.semantic_observables(p["input"])["missing_pattern"] for p in pairs[:-1]],
                    "query_pattern": gen.semantic_observables(pairs[-1]["input"])["missing_pattern"],
                    "query_fits": query_fits,
                    "declared_hook_reasons": gen.lesson_identifiable(pairs[:-1], pairs[-1]),
                    "lesson": pairs,
                })
    result = {
        "task_id": gen.TASK_ID,
        "generator_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
        "rival": "infer the missing orientation of the lowest-color rectangle, then use that orientation for every rectangle",
        "tested_windows": 3 * 18,
        "demo_survivor_count": len(records),
        "query_disagreement_count": sum(not r["query_fits"] for r in records),
        "survivors": records,
    }
    out = Path(__file__).resolve().parents[4] / "checks" / "baseline-first-orientation-shortcut.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "survivors"}, indent=2))
    for row in records:
        print(row["band"], row["start"], row["demo_patterns"], "query", row["query_pattern"], "query_fits", row["query_fits"], "hook", row["declared_hook_reasons"])


if __name__ == "__main__":
    main()
