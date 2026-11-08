from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path.cwd()
TASK = "generic_dense_select_gen1"
SOURCE = ROOT / "generators" / TASK / "generator.py"
OUT = ROOT.parent / "checks" / "audit" / TASK

sys.path.insert(0, str(ROOT / "shared" / "runtime"))
sys.path.insert(0, str(ROOT / "src"))

spec = importlib.util.spec_from_file_location(f"audit_{TASK}", SOURCE)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def threshold_rule(grid):
    """Wrong absolute shortcut: keep every object with at least 9 cells."""
    bg = mod._infer_bg(grid)
    objects = mod.py_objects(grid, bg=bg)
    return mod.erase_objects(
        grid, [obj for obj in objects if obj["size"] <= 8], bg=bg
    )


per_band = {}
all_pairs = 0
all_matches = 0
all_grammar_errors = []
all_hashes = set()
for band in ("easy", "medium", "hard"):
    pairs = matches = 0
    winners = []
    distractors = []
    hashes = set()
    for seed in range(30):
        task = mod.generate_task(seed, difficulty=band)
        for split in ("train", "test"):
            for pair_index, pair in enumerate(task[split]):
                grid = pair["input"]
                errors = mod.strict_canonical_like(grid)
                if errors:
                    all_grammar_errors.append(
                        {"band": band, "seed": seed, "split": split,
                         "pair_index": pair_index, "errors": errors}
                    )
                bg = mod._infer_bg(grid)
                sizes = [obj["size"] for obj in mod.py_objects(grid, bg=bg)]
                winner = max(sizes)
                winners.append(winner)
                distractors.extend(size for size in sizes if size != winner)
                digest = hashlib.sha256(
                    json.dumps(grid, separators=(",", ":")).encode()
                ).hexdigest()
                hashes.add(digest)
                all_hashes.add(digest)
                pairs += 1
                all_pairs += 1
                if threshold_rule(grid) == pair["output"]:
                    matches += 1
                    all_matches += 1
    per_band[band] = {
        "seed_range": "0..29 inclusive",
        "tasks": 30,
        "pairs": pairs,
        "unique_inputs": len(hashes),
        "threshold_matches": matches,
        "threshold_disagreements": pairs - matches,
        "winner_size_range": [min(winners), max(winners)],
        "distractor_size_range": [min(distractors), max(distractors)],
    }

# Relative-maximum concept counterexample. It satisfies every documented
# structural condition except the generator's absolute winner range 10..15.
bg = 1
grid = [[bg] * 16 for _ in range(16)]
placements = [
    (3, [(1, 1), (1, 2), (1, 3)]),
    (2, [(1, 10), (2, 10), (3, 10), (4, 10), (4, 11), (4, 12), (4, 13)]),
    (4, [(6, 1), (6, 2), (6, 3), (6, 4), (6, 5), (6, 6)]),
    (2, [(7, 8), (7, 9), (7, 10), (7, 11),
         (8, 8), (8, 9), (8, 10), (8, 11)]),
    (5, [(10, 1), (10, 2), (10, 3), (10, 4), (10, 5)]),
    (3, [(12, 8), (12, 9), (12, 10), (12, 11)]),
    (4, [(14, 2), (14, 3), (14, 4)]),
]
for color, cells in placements:
    for row, col in cells:
        grid[row][col] = color

intended = mod._apply(grid, bg=bg)
rival = threshold_rule(grid)
reasons = mod.strict_canonical_like(grid)

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.generic.concepts.dense_select import _program_body

program = mod._program_for(bg)
bridge = RacketBridge()
bridge.define_grid("g", grid)
racket_output = bridge.eval_text(_program_body(program))

source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
report = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK,
    "generator_sha256": source_sha,
    "version": mod.VERSION,
    "rule_template_sha256": mod.RULE_HASH,
    "rival": "keep every object with at least 9 cells",
    "per_band": per_band,
    "totals": {
        "tasks": 90,
        "pairs": all_pairs,
        "unique_inputs": len(all_hashes),
        "matches": all_matches,
        "disagreements": all_pairs - all_matches,
        "grammar_errors": len(all_grammar_errors),
    },
    "counterexample": {
        "strict_canonical_like_reasons": reasons,
        "only_absolute_winner_bound_rejected": reasons == [
            "winner size must be in 10..15"
        ],
        "intended_differs_from_rival": intended != rival,
        "racket_matches_python_intended": racket_output == intended,
        "winner_size": 8,
    },
    "reproduced": (
        all_pairs > 0
        and all_matches == all_pairs
        and not all_grammar_errors
        and reasons == ["winner size must be in 10..15"]
        and intended != rival
        and racket_output == intended
    ),
    "classification": (
        "generated-curriculum shortcut and concept-domain restriction; "
        "not an in-grammar wrong label"
    ),
}
OUT.mkdir(parents=True, exist_ok=True)
for name, value in (
    ("input.json", grid),
    ("intended.json", intended),
    ("rival.json", rival),
):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n")
(OUT / "embedded-racket.json").write_text(
    json.dumps(
        {
            "task_id": TASK,
            "generator_sha256": source_sha,
            "rule_template_sha256": mod.RULE_HASH,
            "program": program,
            "input": grid,
            "output": racket_output,
            "matches_python_intended": racket_output == intended,
        },
        indent=2,
        sort_keys=True,
    )
    + "\n"
)
(OUT / "probe-report.json").write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n"
)
print(json.dumps(report, indent=2, sort_keys=True))
raise SystemExit(0 if report["reproduced"] else 1)
