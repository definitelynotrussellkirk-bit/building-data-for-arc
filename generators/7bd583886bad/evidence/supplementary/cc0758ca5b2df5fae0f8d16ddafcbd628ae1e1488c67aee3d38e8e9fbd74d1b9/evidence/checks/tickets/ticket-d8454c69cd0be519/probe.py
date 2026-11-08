#!/usr/bin/env python3
"""One bounded shortcut probe; execute from WORK/repo via review.py run."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import time
from arcpuzzles.parametric_worker import _real_evaluator, _grid
from arcpuzzles.catalog import Catalog

TICKET = "ticket-d8454c69cd0be519"
TASK = "7bd583886bad"
SEED = "e6ab26d523521e00286cf721f6e5f071713a5c61b123a0b1be9d00f551d12241"
SOURCE_SHA = "434095181e0bd349cdd4b1615526f0612757ea8590e8b129ed003e3f166a1ac9"
RULE_HASH = "d516242a1e90"
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2] / "repo"

# This rival follows the canonical shape and offset order but commits to the
# first locally fitting placement. It never revisits that decision. Like the
# canonical rule's no-solution branch, a dead end returns the original input.
def greedy_without_backtracking(grid, shapes):
    remaining = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 8}
    painted = [[0 for _ in row] for row in grid]
    trace = []
    while remaining:
        p = min(remaining)
        chosen = None
        for typ, shape in enumerate(shapes, 1):
            for dr, dc in shape:
                top, left = p[0] - dr, p[1] - dc
                cells = {(top + r, left + c) for r, c in shape}
                if cells <= remaining:
                    chosen = typ, cells
                    break
            if chosen is not None:
                break
        if chosen is None:
            return [row[:] for row in grid], trace, sorted(remaining)
        typ, cells = chosen
        trace.append({"type": typ, "cells": sorted(cells)})
        for r, c in cells:
            painted[r][c] = typ
        remaining -= cells
    return painted, trace, []

def main():
    start = time.monotonic()
    signal.alarm(110)
    source = ROOT / "generators" / TASK / "generator.py"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    assert digest == SOURCE_SHA, (digest, SOURCE_SHA)
    spec = importlib.util.spec_from_file_location("ticket_generator", source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    records = [json.loads(line) for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()]
    records = [row for row in records if row.get("task_id") == TASK]
    programs = {row["program_solution"] for row in records}
    assert len(programs) == 1
    program = programs.pop()
    program_sha = hashlib.sha256(program.encode()).hexdigest()
    registered_rule_hash = Catalog(ROOT).describe(TASK)["rule_hash"]
    assert registered_rule_hash == RULE_HASH, (registered_rule_hash, RULE_HASH)
    identity = {"ticket_id": TICKET, "task_id": TASK, "rule_task_id": TASK,
                "generator_path": "repo/generators/" + TASK + "/generator.py",
                "generator_sha256": digest, "rule_hash": registered_rule_hash,
                "rule_hash_authority": "arcpuzzles.catalog.Catalog.describe",
                "program_sha256": program_sha, "seed": SEED,
                "generator_seed": int(SEED, 16), "seed_mapping": "int(ticket_seed, 16)",
                "canonical_record_sources": sorted(row["source"] for row in records)}
    (OUT / "identity.json").write_text(json.dumps(identity, indent=2) + "\n")
    # An exact retained rule makes the witness inspectable without copying the
    # complete canonical dataset. The probe also verifies live pinned identity.
    (OUT / "canonical.rkt").write_text(program)
    attempts = []
    witness = None
    for sample_index in range(8):
        grid = gen.generate(int(SEED, 16), sample_index)
        errors = gen.self_check(grid)
        assert not errors, errors
        rival, trace, remaining = greedy_without_backtracking(grid, gen.PIECES)
        attempts.append({"sample_index": sample_index, "self_check_errors": errors,
                         "greedy_stuck": bool(remaining), "greedy_placements": len(trace)})
        if not remaining:
            continue
        apply, runtime_identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        try:
            canonical = _grid(apply(program, grid))
        finally:
            bridge.close()
        assert canonical != rival
        mask = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 8}
        wrong_placement = next(step for step in trace
            if any(canonical[r][c] != step["type"] for r, c in step["cells"]))
        witness = {**identity, "sample_index": sample_index, "difficulty": None,
            "overrides": {}, "input": grid, "canonical_output": canonical,
            "rival_output": rival, "rival": "earliest-cell first-local-fit; canonical type/offset order; no backtracking; on dead end return input",
            "greedy_trace": trace, "greedy_remaining_cells_at_dead_end": remaining,
            "first_wrong_placement": wrong_placement,
            "lawfulness": {"self_check_errors": errors,
                "connected_components": len(gen._components(mask)),
                "exact_cover_count_capped_at_2": gen._exact_cover_count(mask, len(grid), len(grid[0]), limit=2)},
            "differing_cells": [[r, c] for r, row in enumerate(canonical) for c, v in enumerate(row) if v != rival[r][c]],
            "authority": runtime_identity,
            "interpretation": "A lawful generated wrong-rule separator, not a peer safety finding. No lesson acceptance or training-admission test was attempted."}
        (OUT / "witness.json").write_text(json.dumps(witness, indent=2) + "\n")
        break
    elapsed = time.monotonic() - start
    summary = {"ticket_id": TICKET, "status": "completed" if witness else "unknown",
        "probe_limit_seconds": 120, "targeted_probes": 1, "sample_limit": 8,
        "attempts": attempts, "probe_elapsed_seconds": elapsed,
        "racket_evaluations": 1 if witness else 0,
        "witness_sample_index": witness["sample_index"] if witness else None,
        "differing_cell_count": len(witness["differing_cells"]) if witness else None,
        "stop_reason": "first lawful Racket-labelled separator retained" if witness else "no separator in eight bounded samples",
        "scope_limit": "One rival only; no peer battery, lesson certificate or overall safety claim."}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True))
    signal.alarm(0)

if __name__ == "__main__":
    main()
