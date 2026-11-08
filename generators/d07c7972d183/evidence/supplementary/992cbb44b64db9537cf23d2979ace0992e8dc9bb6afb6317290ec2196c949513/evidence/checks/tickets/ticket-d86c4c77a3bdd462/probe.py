#!/usr/bin/env python3
"""Seed-bound adversarial witness probe for d07c7972d183."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
ROOT = next(parent / "repo" for parent in HERE.parents if (parent / "repo" / "shared" / "runtime").is_dir())
for path in (ROOT / "shared" / "runtime", ROOT / "src"):
    sys.path.insert(0, str(path))

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.generic.concepts.extraction import _program_body
from reviewer_support import canonical_path, load_selected_generator

TASK_ID = "d07c7972d183"
TICKET_SEED = "74e46bf4820dc57bc9c2585c2036537b1cbc892c5d396e5752949d39e44a0fbd"
PINNED_SOURCE_SHA256 = "2f2f8e0d2b8ef4f8ddd5c3e2b8a36abb07b4e96ef1a2d12eedd01547efada63a"
PINNED_RULE_HASH = "6358a7ca0f4d"


def canonical_row():
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise RuntimeError("canonical row missing")


def width_extension_rival(gen, grid):
    """Plausible canonical shortcut: append one row per input column."""
    return gen._diagnostic_output(grid, height=len(grid) + len(grid[0]))


def apply_racket(program, grid):
    bridge = RacketBridge()
    try:
        bridge.define_grid("g", grid)
        return bridge.eval_text(_program_body(program)), bridge.runtime_identity
    finally:
        bridge.shutdown()


def changed_cells(a, b):
    h = max(len(a), len(b))
    rows = []
    for r in range(h):
        ar = a[r] if r < len(a) else None
        br = b[r] if r < len(b) else None
        if ar != br:
            rows.append(r)
    return rows


def main():
    gen, source_path, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)
    if source_sha256 != PINNED_SOURCE_SHA256:
        raise RuntimeError(f"source drift: {source_sha256}")
    if gen.RULE_HASH != PINNED_RULE_HASH:
        raise RuntimeError(f"rule hash drift: {gen.RULE_HASH}")
    canonical = canonical_row()
    pairs = [*canonical["train"], *canonical["test"]]
    canonical_fit = [width_extension_rival(gen, pair["input"]) == pair["output"] for pair in pairs]

    digest = bytes.fromhex(TICKET_SEED)
    seed = int.from_bytes(digest[:8], "big") & 0x7FFFFFFF
    start = int.from_bytes(digest[8:12], "big") % gen.LESSON_SCHEDULE_PERIOD
    witness = None
    for offset in range(gen.LESSON_SCHEDULE_PERIOD):
        sample_index = (start + offset) % gen.LESSON_SCHEDULE_PERIOD
        grid = gen.generate(seed, sample_index)
        intended = gen._diagnostic_output(grid)
        rival = width_extension_rival(gen, grid)
        if gen.self_check(grid) == [] and intended != rival:
            witness = {
                "seed": seed,
                "sample_index": sample_index,
                "schedule_profile": gen.schedule_profile(seed, sample_index),
                "input": grid,
                "python_intended": intended,
                "rival": rival,
            }
            break
    if witness is None:
        raise RuntimeError("bounded eight-position schedule search found no witness")

    racket, runtime_identity = apply_racket(canonical["program_solution"], witness["input"])
    witness["racket"] = racket
    witness["racket_matches_intended"] = racket == witness["python_intended"]
    witness["rival_differs"] = racket != witness["rival"]
    witness["input_height"] = len(witness["input"])
    witness["input_width"] = len(witness["input"][0])
    witness["least_row_period"] = gen._minimal_row_period(witness["input"])
    witness["correct_output_height"] = len(racket)
    witness["rival_output_height"] = len(witness["rival"])
    witness["differing_row_indices"] = changed_cells(racket, witness["rival"])

    # The real three-demo schedule should expose at least one distinguishing row
    # for every cyclic start, so this shortcut cannot survive a full lesson.
    lesson_rows = []
    for lesson_start in range(gen.LESSON_SCHEDULE_PERIOD):
        demos = [gen.generate(seed, lesson_start + j) for j in range(gen.EXAMPLES_NEEDED)]
        fits = all(width_extension_rival(gen, grid) == gen._diagnostic_output(grid) for grid in demos)
        lesson_rows.append({"start": lesson_start, "fits_all_demos": fits})

    out_dir = HERE.parent
    (out_dir / "input.json").write_text(json.dumps(witness["input"], indent=2) + "\n")
    (out_dir / "racket.json").write_text(json.dumps(racket, indent=2) + "\n")
    (out_dir / "rival.json").write_text(json.dumps(witness["rival"], indent=2) + "\n")
    report = {
        "schema": "adversarial-witness-ticket-v1",
        "ticket_id": "ticket-d86c4c77a3bdd462",
        "task_id": TASK_ID,
        "ticket_seed": TICKET_SEED,
        "source": {"path": str(source_path.relative_to(ROOT)), "sha256": source_sha256},
        "rule_hash": gen.RULE_HASH,
        "rival": {
            "name": "append_input_width_rows",
            "description": "continue the least row period, but set output height to input height plus input width",
            "canonical_fit": {"fits": sum(canonical_fit), "pairs": len(canonical_fit), "by_pair": canonical_fit},
        },
        "witness": {k: v for k, v in witness.items() if k not in {"input", "python_intended", "racket", "rival"}},
        "lesson_schedule": {
            "three_demo_starts": lesson_rows,
            "surviving_starts": [row["start"] for row in lesson_rows if row["fits_all_demos"]],
        },
        "runtime_identity": runtime_identity,
        "artifacts": ["input.json", "racket.json", "rival.json"],
        "status": "completed" if all(canonical_fit) and witness["racket_matches_intended"] and witness["rival_differs"] and not any(row["fits_all_demos"] for row in lesson_rows) else "finding",
        "conclusion": "The width-based height shortcut fits all canonical pairs, but the seed-bound lawful witness and every cyclic three-demo production window refute it.",
    }
    (out_dir / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
