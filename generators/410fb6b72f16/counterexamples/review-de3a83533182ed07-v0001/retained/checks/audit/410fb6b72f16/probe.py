"""Findings-only audit; writes evidence, never edits generator/rule sources."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
TASK = "410fb6b72f16"
SOURCE = ROOT / "repo/generators" / TASK / "generator.py"
sys.path.insert(0, str(ROOT / "repo/shared/runtime"))
spec = importlib.util.spec_from_file_location("audit_target", SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n")

def components(grid):
    seen, result = set(), []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 1 or (r, c) in seen:
                continue
            cells, queue = [], [(r, c)]
            seen.add((r, c))
            while queue:
                p = queue.pop()
                cells.append(p)
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = p[0] + dr, p[1] + dc
                    if (0 <= q[0] < len(grid) and 0 <= q[1] < len(row)
                            and grid[q[0]][q[1]] == 1 and q not in seen):
                        seen.add(q)
                        queue.append(q)
            result.append(sorted(cells))
    return result

def rival(grid):
    """Keep the two largest blue objects; recolor all other blue objects red."""
    comps = sorted(components(grid), key=lambda c: (-len(c), c[0]))
    out = copy.deepcopy(grid)
    for cells in comps[2:]:
        for r, c in cells:
            out[r][c] = 2
    return out

row = next(json.loads(line) for line in
           (ROOT / "repo/shared/data/canonical/puzzles.jsonl").read_text().splitlines()
           if json.loads(line).get("task_id") == TASK)
inputs, records, mirrors = [], [], []
canonical_pairs = row["train"] + [row["test"]]
for i, pair in enumerate(canonical_pairs):
    grid = [[int(c) for c in r] for r in pair["input"]]
    inputs.append(grid)
    mirrors.append([[int(c) for c in r] for r in pair["output"]])
    records.append({"kind": "canonical", "pair_index": i})

for band in ("easy", "medium", "hard"):
    for index in range(20):
        grid = gen.generate(20261005, index, difficulty=band)
        inputs.append(grid)
        mirrors.append(gen.rule_mirror(grid))
        records.append({"kind": "ordinary_generated", "seed": 20261005,
                        "sample_index": index, "difficulty": band, "overrides": {}})

source_index = 24  # medium, seed 20261005, sample_index 1
probe = copy.deepcopy(inputs[source_index])
removed = next(cells for cells in components(probe) if len(cells) == 2)
for r, c in removed:
    probe[r][c] = 0
inputs.append(probe)
mirrors.append(gen.rule_mirror(probe))
records.append({"kind": "canonical_like_recombination", "seed": 20261005,
                "sample_index": 1, "difficulty": "medium", "overrides": {},
                "source_input_index": source_index,
                "mutation": {"operation": "remove the blue domino", "cells": removed}})
for index, (grid, record) in enumerate(zip(inputs, records)):
    record.update({"input_index": index, "validator_result": gen.self_check(grid),
                   "strict_canonical_like_result": gen.strict_canonical_like(grid),
                   "blue_component_sizes": sorted(map(len, components(grid)))})

demos = [{"input": inputs[i], "output": mirrors[i]} for i in (23, 24, 25)]
query = {"input": probe, "output": mirrors[-1]}
state = {
    "task_id": TASK,
    "target_generator_path": str(SOURCE.relative_to(ROOT)),
    "target_generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "selected_rule_sha256": hashlib.sha256(row["program_solution"].encode()).hexdigest(),
    "selected_rule_pinned_hash": gen.RULE_HASH,
    "assignment_sha256": hashlib.sha256((ROOT / "AUDIT_ASSIGNMENT.json").read_bytes()).hexdigest(),
    "seed": 20261005, "sample_index": 1, "overrides": {},
    "records": records,
    "lesson_demo_input_indices": [23, 24, 25],
    "query_input_index": 63,
    "lesson_identifiable_result": gen.lesson_identifiable(demos, query),
    "documented_domain_membership": {
        "ordinary_generation": "Indices 3..62 are exact unmodified generate(seed=20261005, sample_index=0..19, difficulty=easy/medium/hard, overrides={}) returns.",
        "query": "Index 63 deletes only the size-two component of input 24. self_check and strict_canonical_like both accept. It has dimensions and colors in-domain, 2..4 blue singletons, one larger blue component of size 3 or 4. strict_canonical_like explicitly accepts one or two multi-cell components. The written rule applies without ambiguity. It is outside ordinary generator support, which always creates two multi-cell components and includes a domino."
    },
    "scope": "Target generator, selected canonical row, retained target notes, 60 ordinary draws, 3 canonical pairs, and one canonical-like recombination. No source edits; no private runner imports.",
}
write("input.json", inputs)
write("rivaloutput.json", [rival(grid) for grid in inputs])
write("python_mirror.json", mirrors)
write("generation.json", {"records": records, "inputs": inputs})
write("audit_state.json", state)
print(json.dumps({"inputs": len(inputs), "source_index": source_index,
                  "query_component_sizes": records[-1]["blue_component_sizes"],
                  "validator_result": records[-1]["validator_result"],
                  "strict_canonical_like_result": records[-1]["strict_canonical_like_result"],
                  "lesson_identifiable_result": state["lesson_identifiable_result"]}))
