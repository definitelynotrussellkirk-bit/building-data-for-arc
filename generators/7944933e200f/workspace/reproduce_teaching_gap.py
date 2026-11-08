#!/usr/bin/env python3
"""Replay the source-bound seed0/medium/5..8 singleton shortcut witness.

Run through review.py run to supply the portable runtime. Optionally pass a
retained original generator.py with --source; source files are loaded read-only.
The JSON is bounded to the four-pair lesson and binds the exact tested bytes.
Exit1 means the rival fits demonstrations and changes the query; exit0 means
this specific historical lesson is no longer ambiguous.
"""
from collections import Counter
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1] / "generator.py")
args = parser.parse_args()
spec = importlib.util.spec_from_file_location("global_rank_crop_repro", args.source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def rival(grid):
    counts = Counter(value for row in grid for value in row if value)
    minimum = min(counts.values())
    return next([[value]] for row in grid for value in row if value and counts[value] == minimum)


lesson = []
for index in range(5, 9):
    grid = module.generate(0, index, difficulty="medium")
    lesson.append({"sample_index": index, "input": grid, "mirror_output": module.rule_mirror(grid),
                   "rival_output": rival(grid), "observed_profile": module.observe_overrides(grid)})
ambiguous = all(pair["mirror_output"] == pair["rival_output"] for pair in lesson[:3]) and lesson[3]["mirror_output"] != lesson[3]["rival_output"]
print(json.dumps({"source_sha256": hashlib.sha256(args.source.read_bytes()).hexdigest(),
                  "seed": 0, "difficulty": "medium", "rival": "first_minimum_frequency_cell_only",
                  "ambiguous": ambiguous, "lesson": lesson}, sort_keys=True, indent=2))
raise SystemExit(int(ambiguous))
