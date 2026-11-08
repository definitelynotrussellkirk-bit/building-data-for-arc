from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
sys.path[:0] = [str(REPO / "shared/runtime"), str(REPO / "src")]
path = REPO / "generators/95d9a7d908ea/generator.py"
spec = importlib.util.spec_from_file_location("audit_95d9a7d908ea", path)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def signature(grid):
    comps = mod._components(grid)
    rows = []
    for index, (color, cells) in enumerate(comps):
        rows.append({"index": index, "color": color, "size": len(cells),
                     "holes": mod._hole_count(cells), "cells": sorted(map(list, cells))})
    authority = max(rows, key=lambda row: (row["holes"], row["size"]))
    largest = max(rows, key=lambda row: row["size"])
    return rows, authority, largest

samples = []
all_match = True
for seed in range(100):
    for sample_index in range(3):
        grid = mod.generate(seed, sample_index, difficulty="medium")
        rows, authority, largest = signature(grid)
        same = authority["index"] == largest["index"]
        all_match &= same
        if len(samples) < 3:
            samples.append({"seed": seed, "sample_index": sample_index,
                            "components": [{k:v for k,v in row.items() if k != "cells"} for row in rows],
                            "authority_winner": authority["index"],
                            "largest_winner": largest["index"], "same": same})

# Lawful separation: an 8-cell ring has a hole; a 9-cell line is larger but hole-free.
manual = [[0] * 15 for _ in range(6)]
for r, c in [(1,1),(1,2),(1,3),(2,1),(2,3),(3,1),(3,2),(3,3)]: manual[r][c] = 2
for c in range(5,14): manual[4][c] = 4
manual_rows, manual_authority, manual_largest = signature(manual)
result = {
    "task_id": mod.TASK_ID,
    "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    "generated_draws": 300,
    "largest_shortcut_matches_all_generated": all_match,
    "samples": samples,
    "root_cause": "the guaranteed holed motif has at least 8 cells while every distractor has 3-5 cells",
    "manual_lawful_counterexample": {
        "grid": manual,
        "components": [{k:v for k,v in row.items() if k != "cells"} for row in manual_rows],
        "authority_winner": manual_authority["index"],
        "largest_winner": manual_largest["index"],
        "shortcut_disagrees": manual_authority["index"] != manual_largest["index"],
    },
}
assert all_match
assert result["manual_lawful_counterexample"]["shortcut_disagrees"]
out = Path(__file__).with_name("largest_shortcut.json")
out.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k: result[k] for k in ("task_id","generated_draws","largest_shortcut_matches_all_generated","root_cause")}, indent=2))
