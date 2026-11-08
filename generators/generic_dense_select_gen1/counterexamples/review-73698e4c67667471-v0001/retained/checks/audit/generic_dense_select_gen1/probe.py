from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "shared" / "runtime"))
sys.path.insert(0, str(ROOT / "src"))

TASK = "generic_dense_select_gen1"
GEN = ROOT / "generators" / TASK / "generator.py"
OUT = ROOT.parent / "checks" / "audit" / TASK

spec = importlib.util.spec_from_file_location(f"audit_{TASK}", GEN)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def threshold_rule(grid):
    """Wrong shortcut: erase every component of size <= 8."""
    bg = mod._infer_bg(grid)
    objs = mod.py_objects(grid, bg=bg)
    return mod.erase_objects(grid, [obj for obj in objs if obj["size"] <= 8], bg=bg)


bands = ("easy", "medium", "hard")
per_band = {}
all_input_hashes = set()
all_matches = 0
all_pairs = 0
all_grammar_errors = []
for difficulty in bands:
    task_count = pair_count = match_count = 0
    input_hashes = set()
    winner_sizes = []
    distractor_sizes = []
    for seed in range(100):
        task = mod.generate_task(seed, difficulty=difficulty)
        task_count += 1
        for split in ("train", "test"):
            for pair_index, pair in enumerate(task[split]):
                pair_count += 1
                all_pairs += 1
                grid = pair["input"]
                errors = mod.strict_canonical_like(grid)
                if errors:
                    all_grammar_errors.append({
                        "difficulty": difficulty,
                        "seed": seed,
                        "split": split,
                        "pair_index": pair_index,
                        "errors": errors,
                    })
                bg = mod._infer_bg(grid)
                objs = mod.py_objects(grid, bg=bg)
                sizes = [obj["size"] for obj in objs]
                best = max(sizes)
                winner_sizes.append(best)
                distractor_sizes.extend(size for size in sizes if size != best)
                key = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
                input_hashes.add(key)
                all_input_hashes.add(key)
                if threshold_rule(grid) == pair["output"]:
                    match_count += 1
                    all_matches += 1
    per_band[difficulty] = {
        "seed_range": "0..99 inclusive",
        "tasks": task_count,
        "pairs": pair_count,
        "unique_inputs": len(input_hashes),
        "threshold_matches": match_count,
        "threshold_disagreements": pair_count - match_count,
        "winner_size_min": min(winner_sizes),
        "winner_size_max": max(winner_sizes),
        "distractor_size_min": min(distractor_sizes),
        "distractor_size_max": max(distractor_sizes),
    }

# Concept-lawful counterexample satisfying every documented grammar constraint
# except the artificial absolute winner-size range.  The unique relative maximum
# has eight cells; every distractor is smaller.
bg = 1
grid = [[bg] * 16 for _ in range(16)]
placements = [
    (3, [(1, 1), (1, 2), (1, 3)]),
    (2, [(1, 10), (2, 10), (3, 10), (4, 10), (4, 11), (4, 12), (4, 13)]),
    (4, [(6, 1), (6, 2), (6, 3), (6, 4), (6, 5), (6, 6)]),
    (2, [(7, 8), (7, 9), (7, 10), (7, 11), (8, 8), (8, 9), (8, 10), (8, 11)]),
    (5, [(10, 1), (10, 2), (10, 3), (10, 4), (10, 5)]),
    (3, [(12, 8), (12, 9), (12, 10), (12, 11)]),
    (4, [(14, 2), (14, 3), (14, 4)]),
]
for color, cells in placements:
    for r, c in cells:
        grid[r][c] = color

intended = mod._apply(grid, bg=bg)
rival = threshold_rule(grid)
reasons = mod.strict_canonical_like(grid)
objects = [
    {
        "row_major_index": index,
        "color": obj["color"],
        "size": obj["size"],
        "bbox_area": mod._bbox_area(obj),
    }
    for index, obj in enumerate(mod.py_objects(grid, bg=bg))
]

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.generic.concepts.dense_select import _program_body
program = mod._program_for(bg)
bridge = RacketBridge()
bridge.define_grid("g", grid)
racket_output = bridge.eval_text(_program_body(program))

source_sha = hashlib.sha256(GEN.read_bytes()).hexdigest()
specialized_rule_sha = hashlib.sha256(program.encode("utf-8")).hexdigest()
report = {
    "schema": "arcpuzzles-audit-probe-v2",
    "task_id": TASK,
    "generator_sha256": source_sha,
    "generator_version": mod.VERSION,
    "rule_template_sha256": mod.RULE_HASH,
    "seed_range": "0..99 inclusive per difficulty band",
    "bands": list(bands),
    "per_band": per_band,
    "totals": {
        "tasks": 300,
        "pairs": all_pairs,
        "unique_inputs": len(all_input_hashes),
        "threshold_matches": all_matches,
        "threshold_disagreements": all_pairs - all_matches,
        "grammar_errors": len(all_grammar_errors),
    },
    "finding": (
        "The undeclared absolute shortcut 'erase every component with <=8 cells' "
        "matches every generated label because winners are always 10..15 cells and "
        "all distractors are always 3..8 cells."
    ),
    "counterexample": {
        "background": bg,
        "dimensions": [len(grid), len(grid[0])],
        "objects": objects,
        "strict_canonical_like_reasons": reasons,
        "all_grammar_constraints_except_absolute_winner_size": reasons == ["winner size must be in 10..15"],
        "intended_differs_from_threshold_rival": intended != rival,
        "racket_matches_python_intended": racket_output == intended,
        "specialized_program_sha256": specialized_rule_sha,
    },
    "reproduced": (
        all_pairs > 0
        and all_matches == all_pairs
        and not all_grammar_errors
        and reasons == ["winner size must be in 10..15"]
        and intended != rival
        and racket_output == intended
    ),
    "scope": (
        "The exact counterexample is lawful for the stated relative-maximum concept "
        "but intentionally outside the current generated lesson grammar only on winner size; "
        "there is no in-grammar disagreement because the size gap defines the shortcut."
    ),
}

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
(OUT / "intended.json").write_text(json.dumps(intended, indent=2) + "\n")
(OUT / "rival.json").write_text(json.dumps(rival, indent=2) + "\n")
(OUT / "probe-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
(OUT / "embedded-racket.json").write_text(json.dumps({
    "schema": "arcpuzzles-embedded-racket-audit-v1",
    "task_id": TASK,
    "generator_sha256": source_sha,
    "rule_template_sha256": mod.RULE_HASH,
    "specialized_program_sha256": specialized_rule_sha,
    "program": program,
    "input": grid,
    "output": racket_output,
    "matches_python_intended": racket_output == intended,
    "command": "python3 review.py run python3 ../checks/audit/generic_dense_select_gen1/probe.py",
    "cwd": str(ROOT),
}, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, indent=2, sort_keys=True))
raise SystemExit(0 if report["reproduced"] else 1)
