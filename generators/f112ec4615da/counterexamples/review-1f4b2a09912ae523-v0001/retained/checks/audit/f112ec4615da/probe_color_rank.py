"""Bounded authoring audit of a positional rule versus an audit-only color rival."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "f112ec4615da"
ROOT = find_root(__file__)
OUT = Path(__file__).resolve().parent
gen, source, source_hash = load_selected_generator(TASK, root=ROOT)


def overlay(grid):
    hh, hw = len(grid)//2, len(grid[0])//2
    return [[next((v for v in (grid[r][c+hw], grid[r+hh][c], grid[r+hh][c+hw], grid[r][c]) if v), 0)
             for c in range(hw)] for r in range(hh)]


def min_then_max(grid):
    """Ignore quadrant priority: minimum foreground wins, else largest color."""
    minimum = min(v for row in grid for v in row if v)
    hh, hw = len(grid)//2, len(grid[0])//2
    result = []
    for r in range(hh):
        row = []
        for c in range(hw):
            values = (grid[r][c], grid[r][c+hw], grid[r+hh][c], grid[r+hh][c+hw])
            row.append(minimum if minimum in values else max(values))
        result.append(row)
    return result


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n")


canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
with canonical_path(ROOT).open() as handle:
    authority = next(json.loads(line) for line in handle if line.strip()
                     and json.loads(line).get("task_id") == TASK)
rule = authority["program_solution"]
report = {
    "task_id": TASK, "intent": "diagnostic_probe", "phase": "audit",
    "generator_sha256": source_hash,
    "generator_version": gen.VERSION,
    "rule_sha256": hashlib.sha256(rule.encode()).hexdigest(),
    "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "invocation": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]},
    "declared_CANONICAL_SHORTCUTS": list(getattr(gen, "CANONICAL_SHORTCUTS", ())),
    "declared_LESSON_COMPETITORS": list(getattr(gen, "LESSON_COMPETITORS", ())),
    "rival": {"name": "audit_min_foreground_then_numeric_max", "origin": "new audit-only hypothesis; not claimed as a generator declaration",
              "definition": "At each corresponding quadrant cell, choose the global minimum nonzero input color if present; otherwise choose the maximum of the four cell values."},
    "canonical_retained_label_matches": [min_then_max(pair["input"]) == pair["output"] for pair in canonical],
    "search_policy": {"seed_range": [0, 2047], "stop_at_first_counterexample": True,
                      "demonstrations": 2, "query_count": 1, "sample_indices": [0, 1, 2],
                      "difficulty": None, "overrides": {"grid_h": 6, "grid_w": 6},
                      "search_labels": "independent Python overlay only; retained witness requires separate public Racket apply"},
}
draw_count = 0
found = None
for seed in range(2048):
    pairs = []
    for index in range(3):
        grid = gen.generate(seed, index, grid_h=6, grid_w=6)
        draw_count += 1
        actual = overlay(grid)
        rival = min_then_max(grid)
        pair = {"sample_index": index, "input": grid, "python_reference_prediction": actual,
                "rival_output": rival, "self_check": gen.self_check(grid),
                "observed_overrides": gen.observe_overrides(grid), "rival_exact": rival == actual}
        pairs.append(pair)
        if index < 2 and not pair["rival_exact"]:
            break
    if len(pairs) == 3 and all(pair["rival_exact"] for pair in pairs[:2]) and not pairs[2]["rival_exact"]:
        found = {"seed": seed, "pairs": pairs}
        break
report["examined_seed_range"] = [0, seed]
report["generated_input_count"] = draw_count
report["candidate_found"] = found is not None
report["lesson"] = found
if found:
    inputs = [pair["input"] for pair in canonical] + [pair["input"] for pair in found["pairs"]]
    write("input.json", {"inputs": inputs})
    report["apply_input_mapping"] = [{"index": i, "kind": "canonical", "split": pair["split"], "pair_index": pair["pair_index"]}
                                     for i, pair in enumerate(canonical)] + [
        {"index": len(canonical)+i, "kind": "lesson_demo" if i < 2 else "lesson_query", "sample_index": i}
        for i in range(3)]
write("probe.json", report)
print(json.dumps({"candidate_found": report["candidate_found"], "seed": found["seed"] if found else None,
                  "canonical_matches": sum(report["canonical_retained_label_matches"]),
                  "canonical_pairs": len(canonical), "generated_input_count": draw_count}))
