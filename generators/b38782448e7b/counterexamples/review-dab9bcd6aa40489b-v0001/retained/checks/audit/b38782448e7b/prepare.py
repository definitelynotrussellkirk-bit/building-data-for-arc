"""Materialize one bounded, source-bound audit batch; no private runners."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from rival import solve

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2] / "repo"
TASK = "b38782448e7b"
SOURCE = REPO / "generators" / TASK / "generator.py"
EXPECTED_SOURCE_HASH = "b345f8ffb2fb6be75bc557cf304060d457ee3295388edb327a2ca8bb3c01f29e"


def write(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2) + "\n")


def digest(data):
    return hashlib.sha256(data).hexdigest()


assert digest(SOURCE.read_bytes()) == EXPECTED_SOURCE_HASH
spec = importlib.util.spec_from_file_location("audit_generator_b38782448e7b", SOURCE)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

rows = [json.loads(line) for line in (REPO / "shared/data/canonical/puzzles.jsonl").open()
        if '"b38782448e7b"' in line]
rows = [row for row in rows if row.get("task_id") == TASK]
rules = {row["program_solution"] for row in rows}
assert len(rules) == 1
rule = next(iter(rules))
rule_hash = digest(" ".join(rule.split()).encode())[:12]
assert rule_hash == "06479b7ecc39"
canonical = next(row for row in rows if row["source"] == "training")

grids, cases, rivals = [], [], []


def add(grid, metadata, expected=None):
    bg_counts = Counter(v for row in grid for v in row)
    bg = bg_counts.most_common(1)[0][0]
    h, w = len(grid), len(grid[0])
    markers = [c for c in range(w)
               if grid[0][c] != bg and (h < 2 or grid[0][c] != grid[1][c])]
    off_marker = [(r, c) for r in range(1, h) for c in range(w)
                  if c not in markers and grid[r][c] != bg]
    before = json.dumps(grid)
    errors = module.self_check(grid, difficulty=metadata.get("difficulty"))
    assert json.dumps(grid) == before, "self_check mutated input"
    case = dict(index=len(grids), **metadata, dimensions=[h, w], background=bg,
                background_unique_mode=sum(n == bg_counts[bg] for n in bg_counts.values()) == 1,
                markers=markers, off_marker_colored_body_count=len(off_marker),
                self_check_errors=errors, self_check_accepted=not errors,
                input_sha256=digest(json.dumps(grid, separators=(",", ":")).encode()))
    if expected is not None:
        case["canonical_expected_output"] = expected
        case["canonical_task_domain"] = True
        case["emitted_default_support"] = False
        case["documented_invariants_satisfied"] = not errors
        case["documented_domain_note"] = (
            "Supplied canonical pair, satisfying the stated size/marker/body invariants. "
            "Colored regions outside marker columns have no generation axis and cannot be emitted."
        )
    else:
        case["emitted_default_support"] = True
        case["canonical_task_domain"] = None
        case["documented_invariants_satisfied"] = not errors
    grids.append(grid)
    cases.append(case)
    rivals.append({"index": case["index"], "case_id": case["case_id"], "output": solve(grid)})


for split in ("train", "test"):
    for index, pair in enumerate(canonical[split]):
        add(pair["input"], {"kind": "canonical", "case_id": f"training:{split}:{index}",
                            "source": "training", "split": split, "pair_index": index},
            expected=pair["output"])

for difficulty in ("easy", "medium", "hard"):
    for seed in range(8):
        add(module.generate(seed, 0, difficulty=difficulty),
            {"kind": "generated", "case_id": f"{difficulty}:seed={seed}:sample=0",
             "difficulty": difficulty, "seed": seed, "sample_index": 0, "overrides": {}})

write("input.json", grids)
write("cases.json", cases)
write("rival.json", {"task_id": TASK, "rival": "erase_unmarked_body", "results": rivals})
write("identity.json", {
    "task_id": TASK, "generator_path": str(SOURCE),
    "generator_sha256": EXPECTED_SOURCE_HASH,
    "canonical_rule_hash": rule_hash, "rule_text_sha256": digest(rule.encode()),
    "rule": rule, "canonical_rows": len(rows),
    "canonical_original_pairs": 3, "augmented_rows_repeat_original_pairs": True,
    "generated_sample_count": 24,
    "seed_range_inclusive": [0, 7], "sample_index": 0,
    "difficulties": ["easy", "medium", "hard"], "overrides": {},
    "generation_api": "generator.generate(seed, 0, difficulty=band)",
    "not_run": ["production lesson sampler", "full battery", "override sweep"],
})
print(json.dumps({"input_count": len(grids), "generated_count": 24,
                  "canonical_count": 3,
                  "self_check_accepted": sum(case["self_check_accepted"] for case in cases),
                  "generated_off_marker_body_counts": sorted({case["off_marker_colored_body_count"]
                       for case in cases if case["kind"] == "generated"}),
                  "canonical_off_marker_body_counts": [case["off_marker_colored_body_count"]
                       for case in cases if case["kind"] == "canonical"]}, indent=2))
