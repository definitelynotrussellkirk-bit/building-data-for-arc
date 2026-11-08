#!/usr/bin/env python3
"""One lawful witness against a canonical-left-only reflection shortcut."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve()
REPO = HERE.parents[3] / "repo"
for path in (REPO / "shared" / "runtime", REPO / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, load_selected_generator

TICKET_ID = "ticket-9db99d391dfc3516"
TASK_ID = "29c3f342b62c"
PINNED_SEED = "607a618fabec1770d5786cd05bb3868642ebec39cd72bac39ebca4ceb7f20cd9"
EXPECTED_SHA = "a29db6fb193428cff1e92298066a810a8b0f92bc13c7994d897cf7a92da550fa"
RULE_HASH = "a1a5d656635f"


def _canonical_program() -> str:
    with canonical_path(REPO).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise KeyError(TASK_ID)


def _guide_and_sources(grid):
    h, w = len(grid), len(grid[0])
    guides = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(guides) != 1:
        return None, [], [f"expected one guide, found {len(guides)}"]
    guide = guides[0]
    sources = [
        (r, c, grid[r][c])
        for r in range(h)
        for c in range(w)
        if grid[r][c] not in (0, 5)
    ]
    sides = {"left" if c < guide else "right" if c > guide else "guide" for _, c, _ in sources}
    reasons = []
    if not sources:
        reasons.append("no source cells")
    if len(sides) != 1 or "guide" in sides:
        reasons.append(f"sources are not confined to one non-guide side: {sorted(sides)}")
    for r, c, _ in sources:
        mirror = 2 * guide - c
        if not 0 <= mirror < w:
            reasons.append(f"source {(r, c)} has out-of-bounds mirror {mirror}")
    return guide, sources, reasons


def _left_only_shortcut(grid, guide):
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(guide):
            value = grid[r][c]
            if value not in (0, 5):
                mirror = 2 * guide - c
                if 0 <= mirror < w:
                    out[r][mirror] = value
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    module, source, digest = load_selected_generator(TASK_ID, root=REPO)
    base_seed = int(PINNED_SEED[:16], 16) & 0x7FFFFFFF

    chosen = None
    for offset in range(64):
        seed = (base_seed + offset) & 0x7FFFFFFF
        grid = module.generate(seed, offset % 8, difficulty="hard")
        guide, sources, independent_reasons = _guide_and_sources(grid)
        if not independent_reasons and sources and all(c > guide for _, c, _ in sources):
            chosen = (offset, seed, grid, guide, sources)
            break
    if chosen is None:
        raise RuntimeError("no lawful right-side witness found in 64 deterministic draws")
    offset, seed, grid, guide, sources = chosen

    bridge = RacketBridge()
    try:
        bridge.define_grid("g", grid)
        wrapped_rule = wrap_rule(_canonical_program())
        truth = bridge.eval_text(f"({wrapped_rule} g)")
    finally:
        bridge.shutdown()
    shortcut = _left_only_shortcut(grid, guide)
    differences = [
        {"row": r, "col": c, "truth": truth[r][c], "shortcut": shortcut[r][c]}
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if truth[r][c] != shortcut[r][c]
    ]
    generator_errors = module.self_check(grid)
    independent_guide, independent_sources, independent_reasons = _guide_and_sources(grid)
    passed = (
        digest == EXPECTED_SHA
        and generator_errors == []
        and independent_reasons == []
        and independent_guide == guide
        and independent_sources == sources
        and all(c > guide for _, c, _ in sources)
        and bool(differences)
    )
    report = {
        "ticket_id": TICKET_ID,
        "type": "adversarial_witness",
        "consumer": "target_current_audit",
        "task_id": TASK_ID,
        "pinned_seed": PINNED_SEED,
        "derived_base_seed": base_seed,
        "selected_offset": offset,
        "selected_seed": seed,
        "sample_index": offset % 8,
        "source_path": str(source.relative_to(REPO)),
        "source_sha256": digest,
        "expected_source_sha256": EXPECTED_SHA,
        "rule_hash": RULE_HASH,
        "shortcut": (
            "mirror only non-{0,5} cells left of the guide to the right; this fits "
            "the supplied canonical demonstrations, whose sources are all left-sided"
        ),
        "lawful_witness": {
            "input": grid,
            "guide_col": guide,
            "source_cells": [list(cell) for cell in sources],
            "generator_self_check": generator_errors,
            "independent_grammar_reasons": independent_reasons,
            "racket_output": truth,
            "left_only_shortcut_output": shortcut,
            "differing_cells": differences,
            "input_sha256": hashlib.sha256(
                json.dumps(grid, separators=(",", ":")).encode()
            ).hexdigest(),
        },
        "passed": passed,
        "elapsed_seconds": time.monotonic() - started,
        "conclusion": (
            "A lawful generated right-side scene forces bidirectional reflection and "
            "refutes the canonical-left-only shortcut under the exact Racket rule."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "passed": passed,
        "selected_offset": offset,
        "guide_col": guide,
        "source_cells": len(sources),
        "differing_cells": len(differences),
        "source_sha256": digest,
        "elapsed_seconds": report["elapsed_seconds"],
    }, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
