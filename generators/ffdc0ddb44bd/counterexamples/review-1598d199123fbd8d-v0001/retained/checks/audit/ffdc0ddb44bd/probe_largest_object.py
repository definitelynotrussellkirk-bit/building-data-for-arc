#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
WORK = HERE.parents[3]
REPO = WORK / "repo"
sys.path[:0] = [str(REPO / "src"), str(REPO / "shared" / "runtime")]

from puzzle_generators.helpers.selfcheck import components
from reviewer_support import canonical_pairs

TASK_ID = "ffdc0ddb44bd"
GEN_PATH = REPO / "generators" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GEN_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def crop(comp):
    r1, c1, r2, c2 = comp["bbox"]
    cells = set(comp["cells"])
    return [
        [8 if (row, col) in cells else 0 for col in range(c1, c2 + 1)]
        for row in range(r1, r2 + 1)
    ]


def largest_object_shortcut(grid):
    comps = sorted(
        components(grid, colors={2, 3, 4, 5, 6}),
        key=lambda comp: (comp["bbox"][0], comp["bbox"][1]),
    )
    largest = max(len(comp["cells"]) for comp in comps)
    return crop(next(comp for comp in comps if len(comp["cells"]) == largest))


canonical = canonical_pairs(TASK_ID, root=REPO)
canonical_rows = [
    {
        "index": index,
        "shortcut_matches": largest_object_shortcut(pair["input"]) == pair["output"],
    }
    for index, pair in enumerate(canonical)
]

bands = {}
first_ambiguity = None
for band in ("easy", "medium", "hard"):
    generated_matches = 0
    generated_total = 0
    ambiguous_rotations = 0
    rotations_checked = 0
    for start in range(1000):
        pairs = []
        for offset in range(4):
            grid = GEN.generate(123456 + start, start + offset, difficulty=band)
            truth = GEN.rule_mirror(deepcopy(grid))
            shortcut = largest_object_shortcut(deepcopy(grid))
            pairs.append({"input": grid, "output": truth, "shortcut": shortcut})
            generated_total += 1
            generated_matches += shortcut == truth
        for query_index in range(4):
            demo_indices = [index for index in range(4) if index != query_index]
            survives = all(
                pairs[index]["shortcut"] == pairs[index]["output"]
                for index in demo_indices
            )
            differs_on_query = (
                pairs[query_index]["shortcut"] != pairs[query_index]["output"]
            )
            rotations_checked += 1
            if survives and differs_on_query:
                ambiguous_rotations += 1
                if first_ambiguity is None:
                    first_ambiguity = {
                        "band": band,
                        "seed": 123456 + start,
                        "start": start,
                        "query_index": query_index,
                        "demo_indices": demo_indices,
                        "pair_match_vector": [
                            pair["shortcut"] == pair["output"] for pair in pairs
                        ],
                        "pairs": pairs,
                    }
    bands[band] = {
        "generated_shortcut_matches": generated_matches,
        "generated_examples": generated_total,
        "ambiguous_rotations": ambiguous_rotations,
        "rotations_checked": rotations_checked,
    }

result = {
    "schema": "arc-audit-probe-v1",
    "task_id": TASK_ID,
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "rival": (
        "crop the first row-major object having the largest cell count; "
        "this ignores translation-normalized shape frequency"
    ),
    "canonical": canonical_rows,
    "bands": bands,
    "first_ambiguity": first_ambiguity,
    "limitations": (
        "Python rule_mirror supplies generated labels in this probe; retained "
        "Racket apply evidence separately checks the exact four-pair witness."
    ),
}
OUT = HERE.with_name("largest_object_probe.json")
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
if first_ambiguity is None:
    raise SystemExit("no ambiguity reproduced")
RACKET_INPUT = HERE.with_name("largest_object_racket_inputs.json")
RACKET_INPUT.write_text(json.dumps({"inputs": [p["input"] for p in first_ambiguity["pairs"]]}, indent=2) + "\n")
print(json.dumps({"output": str(OUT), "racket_input": str(RACKET_INPUT), "bands": bands}, indent=2))
