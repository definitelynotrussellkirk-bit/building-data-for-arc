"""Read-only audit. Run from WORK/repo through the packet's public wrapper."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

TASK = "3e2b303f4cf7"
OUT = Path(__file__).resolve().parent
ROOT = Path.cwd()
SOURCE = ROOT / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("audit_generator", SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

def global_horizontal_priority(grid):
    # Deliberately rival semantic order: vertical rectangles, then horizontal.
    # Use the target's pair extraction, changing only processing order.
    return gen._apply_pairs(grid, orientation_order=("v", "h", "off"))

def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()

rows = [json.loads(line) for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()]
canonical = [row for row in rows if row.get("task_id") == TASK]
pairs = [pair for row in canonical for split in ("train", "test") for pair in row.get(split, []) if "output" in pair]
rule = canonical[0]["program_solution"]
rule_digest = hashlib.sha256(" ".join(rule.split()).encode()).hexdigest()
source_digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()

grid = [[0] * 10 for _ in range(10)]
for color, tops in ((2, ((2, 0), (2, 8))), (3, ((2, 4), (8, 4)))):
    for top_r, top_c in tops:
        for r in (top_r, top_r + 1):
            for c in (top_c, top_c + 1):
                grid[r][c] = color
reflected = list(reversed(copy.deepcopy(grid)))

records = []
unique = set()
for band in ("easy", "medium", "hard"):
    for index in range(64):
        draw = gen.generate(730101, index, difficulty=band)
        unique.add(digest(draw))
        records.append({"difficulty": band, "seed": 730101, "sample_index": index,
                        "overrides": {}, "input_sha256": digest(draw),
                        "accepted": not gen.self_check(draw),
                        "rival_matches_mirror": global_horizontal_priority(draw) == gen.rule_mirror(draw)})

demo_grids = [gen.generate(730101, i, difficulty="medium") for i in range(3)]
demos = [{"input": draw, "output": gen.rule_mirror(draw)} for draw in demo_grids]
query = {"input": grid, "output": gen.rule_mirror(grid)}
inputs = [grid, reflected, *demo_grids, *[pair["input"] for pair in pairs]]
(OUT / "input.json").write_text(json.dumps(inputs, indent=2) + "\n")
result = {
    "task_id": TASK, "generator_sha256": source_digest,
    "rule_hash": rule_digest[:12], "normalized_rule_sha256": rule_digest,
    "constructed_query": {"seed": None, "sample_index": None, "overrides": None,
        "input": grid, "self_check": gen.self_check(grid),
        "strict_canonical_like": gen.strict_canonical_like(grid),
        "observed_axes": gen.observe_overrides(grid),
        "mirror_output": gen.rule_mirror(grid), "rival_output": global_horizontal_priority(grid),
        "differing_cells": [[r, c] for r in range(10) for c in range(10)
                             if gen.rule_mirror(grid)[r][c] != global_horizontal_priority(grid)[r][c]]},
    "reflection": {"input": reflected, "self_check": gen.self_check(reflected),
                   "strict_canonical_like": gen.strict_canonical_like(reflected),
                   "mirror_output": gen.rule_mirror(reflected),
                   "reflected_original_output": list(reversed(gen.rule_mirror(grid))),
                   "commutes_with_mirror": gen.rule_mirror(reflected) == list(reversed(gen.rule_mirror(grid)))},
    "canonical": {"count": len(pairs), "pairs": pairs, "accepted_count": sum(not gen.self_check(p["input"]) for p in pairs),
                  "mirror_matches_labels": sum(gen.rule_mirror(p["input"]) == p["output"] for p in pairs),
                  "rival_matches_labels": sum(global_horizontal_priority(p["input"]) == p["output"] for p in pairs)},
    "generated": {"seed": 730101, "sample_index_range_inclusive": [0, 63],
                  "bands": ["easy", "medium", "hard"], "overrides": {},
                  "count": len(records), "unique_input_count": len(unique),
                  "accepted_count": sum(r["accepted"] for r in records),
                  "rival_matches_mirror_count": sum(r["rival_matches_mirror"] for r in records),
                  "records": records},
    "lesson": {"demonstrations": demos, "query": query,
               "demo_generation": {"seed": 730101, "sample_indices": [0, 1, 2], "difficulty": "medium", "overrides": {}},
               "lesson_identifiable_errors": gen.lesson_identifiable(demos, query),
               "rival_fits_all_demos": all(global_horizontal_priority(p["input"]) == p["output"] for p in demos),
               "rival_differs_on_query": global_horizontal_priority(grid) != query["output"]},
    "input_batch_mapping": ["constructed_query", "vertical_reflection", "demo_0", "demo_1", "demo_2", "canonical_0", "canonical_1", "canonical_2", "canonical_3"],
    "limitations": ["Query is validator/strict-domain accepted, but is not reachable from the generator's fixed endpoint templates.",
                    "192 ordinary rival comparisons use the Python mirror; separate public apply verifies the retained nine-grid batch."]
}
(OUT / "probe.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"generator_sha256": source_digest, "rule_hash": result["rule_hash"],
                  "canonical_count": len(pairs), "canonical_rival_matches": result["canonical"]["rival_matches_labels"]}))
print(json.dumps({"generated_count": len(records), "unique": len(unique), "matches": result["generated"]["rival_matches_mirror_count"], "validator": result["constructed_query"]["self_check"], "strict": result["constructed_query"]["strict_canonical_like"], "lesson_errors": result["lesson"]["lesson_identifiable_errors"], "differing_cells": result["constructed_query"]["differing_cells"]}))
