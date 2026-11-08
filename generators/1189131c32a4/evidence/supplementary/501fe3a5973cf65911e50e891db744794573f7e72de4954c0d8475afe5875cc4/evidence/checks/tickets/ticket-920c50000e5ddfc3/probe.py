#!/usr/bin/env python3
"""One pinned tie-order witness for ticket-920c50000e5ddfc3."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import time

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
sys.path[:0] = [str(REPO / "src"), str(REPO / "shared/runtime")]
TASK = "1189131c32a4"
TICKET = "ticket-920c50000e5ddfc3"
PINNED_SEED = "e788e801416d1b40e9aa850f1bbea79094e74a6adbb2413f1ff11705bd20d4e6"
SOURCE = REPO / f"generators/{TASK}/generator.py"
EXPECTED_SOURCE = "563d9029027d65a06a2c7c01716171eb39685c7284cdb16d6024f6181cb74c8d"
EXPECTED_RULE = "cb24e3652642"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def grid_hash(grid) -> str:
    return sha(json.dumps(grid, separators=(",", ":")).encode())


def load(path: Path):
    spec = importlib.util.spec_from_file_location("ticket_1189131c32a4", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def ascending_tie_rings(grid):
    counts = Counter(cell for row in grid for cell in row if cell != 7)
    ranked = sorted(counts, key=lambda color: (-counts[color], color))
    n = len(ranked)
    center = n - 1
    return [
        [ranked[n - 1 - max(abs(r - center), abs(c - center))] for c in range(2 * n - 1)]
        for r in range(2 * n - 1)
    ]


started = time.monotonic()
assert sha(SOURCE.read_bytes()) == EXPECTED_SOURCE
gen = load(SOURCE)
assert gen.RULE_HASH == EXPECTED_RULE
row = next(
    json.loads(line)
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
    if json.loads(line).get("task_id") == TASK
)
program = row["program_solution"]
assert sha(" ".join(program.split()).encode())[:12] == EXPECTED_RULE
pairs = row["train"] + ([row["test"]] if isinstance(row["test"], dict) else row["test"])
canonical_shortcut_matches = [ascending_tie_rings(pair["input"]) == pair["output"] for pair in pairs]

generation_seed = int(PINNED_SEED[:16], 16)
grid = gen.generate(generation_seed, 0, difficulty="medium", scene_profile="tie_two_way")
analysis = gen._analysis(grid)
assert analysis["errors"] == [] and analysis["scene_profile"] == "tie_two_way"
facts = analysis["facts"]
tie_count = next(count for count, frequency in Counter(facts["counts"].values()).items() if frequency == 2)
tied_colors = sorted(color for color, count in facts["counts"].items() if count == tie_count)
correct = gen.rule_mirror(grid)
rival = ascending_tie_rings(grid)

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

wrapped = wrap_rule(program)
with RacketBridge(timeout=30.0) as bridge:
    bridge.define_grid("ticket-grid", grid)
    racket = bridge.eval_text(f"({wrapped} ticket-grid)")
    runtime = bridge.runtime_identity

differences = [
    {"row": r, "col": c, "canonical": racket[r][c], "shortcut": rival[r][c]}
    for r in range(len(racket))
    for c in range(len(racket[0]))
    if racket[r][c] != rival[r][c]
]
status = "completed" if all(canonical_shortcut_matches) and racket == correct and differences else "unknown"
report = {
    "schema": "arc-ticket-adversarial-witness-v1",
    "ticket_id": TICKET,
    "type": "adversarial_witness",
    "status": status,
    "task_id": TASK,
    "source_sha256": EXPECTED_SOURCE,
    "rule_hash": EXPECTED_RULE,
    "assigned_seed": PINNED_SEED,
    "generation_seed": generation_seed,
    "sample_index": 0,
    "difficulty": "medium",
    "scene_profile": "tie_two_way",
    "shortcut": "rank by descending frequency but use ascending numeric color order for equal counts",
    "canonical_shortcut_matches": canonical_shortcut_matches,
    "canonical_pairs_checked": len(pairs),
    "self_check_errors": gen.self_check(grid),
    "counts": facts["counts"],
    "canonical_ranked_colors": facts["ranked"],
    "shortcut_ranked_colors": sorted(facts["counts"], key=lambda color: (-facts["counts"][color], color)),
    "tie_count": tie_count,
    "tied_colors": tied_colors,
    "input_sha256": grid_hash(grid),
    "canonical_output_sha256": grid_hash(racket),
    "shortcut_output_sha256": grid_hash(rival),
    "racket_matches_python_mirror": racket == correct,
    "different_cells": differences,
    "racket": runtime,
    "witness": {"input": grid, "canonical_output": racket, "shortcut_output": rival},
    "summary": (
        "Retained a lawful tie_two_way witness: ascending numeric tie order fits all four canonical pairs but differs from protected Racket on this generated scene."
        if status == "completed" else
        "The one pinned tie-order probe did not produce a complete lawful discriminator."
    ),
    "scope": "one pinned seed, one declared profile, one shortcut, four canonical pairs; no lesson census or peer battery",
    "elapsed_seconds": time.monotonic() - started,
}
(HERE / "witness.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({k: report[k] for k in ("status", "summary", "canonical_pairs_checked", "different_cells", "elapsed_seconds")}, sort_keys=True))
