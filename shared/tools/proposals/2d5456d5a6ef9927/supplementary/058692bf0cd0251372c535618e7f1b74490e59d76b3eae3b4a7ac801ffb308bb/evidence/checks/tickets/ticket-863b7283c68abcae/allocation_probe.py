#!/usr/bin/env python3
"""One bounded source-bound 3-demo/4-query allocation probe for 9e204e7ff3a2."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

from arcpuzzles import Catalog
from reviewer_support import find_root

TASK_ID = "9e204e7ff3a2"
TICKET_ID = "ticket-863b7283c68abcae"
TICKET_SEED = "20e22b8b9d86938f5432d86d1c9f34ad9984754609ab5521d0d3222e835b01c4"
SEED = int(TICKET_SEED[:16], 16)
DEMO_COUNT = 3
QUERY_COUNT = 4
OUT = Path(__file__).resolve().parent
ROOT = find_root(__file__)
GEN_PATH = ROOT / "generators" / TASK_ID / "generator.py"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def packed(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def ud_complete(grid):
    out = deepcopy(grid)
    h = len(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0 and grid[h - 1 - r][c] != 0:
                out[r][c] = grid[h - 1 - r][c]
    return out


def lr_complete(grid):
    out = deepcopy(grid)
    w = len(grid[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0 and grid[r][w - 1 - c] != 0:
                out[r][c] = grid[r][w - 1 - c]
    return out


def top_to_bottom_only(grid):
    out = deepcopy(grid)
    h = len(grid)
    for r in range((h + 1) // 2, h):
        for c, value in enumerate(grid[r]):
            if value == 0 and grid[h - 1 - r][c] != 0:
                out[r][c] = grid[h - 1 - r][c]
    return out


def bottom_to_top_only(grid):
    out = deepcopy(grid)
    h = len(grid)
    for r in range(0, h // 2):
        for c, value in enumerate(grid[r]):
            if value == 0 and grid[h - 1 - r][c] != 0:
                out[r][c] = grid[h - 1 - r][c]
    return out


def overwrite_from_top(grid):
    out = deepcopy(grid)
    h = len(grid)
    for r in range(h // 2):
        mr = h - 1 - r
        for c in range(len(grid[0])):
            out[mr][c] = grid[r][c]
    return out


def load_generator():
    spec = importlib.util.spec_from_file_location("allocation_target", GEN_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


started = time.perf_counter()
report = {
    "schema": "allocation-quality-probe-v1",
    "ticket_id": TICKET_ID,
    "task_id": TASK_ID,
    "ticket_seed": TICKET_SEED,
    "episode_seed": SEED,
    "demo_count": DEMO_COUNT,
    "query_count": QUERY_COUNT,
    "query_answers_used_for_rival_elimination": False,
    "source_sha256": sha(GEN_PATH.read_bytes()),
    "probe_sha256": sha(Path(__file__).read_bytes()),
}
try:
    gen = load_generator()
    grids = [gen.generate(SEED, i, difficulty=None) for i in range(DEMO_COUNT + QUERY_COUNT)]
    validation = [gen.self_check(grid) for grid in grids]
    if any(validation):
        raise AssertionError(f"self_check rejected generated input: {validation}")
    if len({packed(grid) for grid in grids}) != len(grids):
        raise AssertionError("episode contains duplicate inputs")

    applied = Catalog(ROOT).apply(TASK_ID, grids, timeout=180)
    if not applied.get("rule_hash_matches_catalog"):
        raise AssertionError("Racket rule hash mismatch")
    if applied.get("rule_hash") != "892d64eecd2e":
        raise AssertionError(f"unexpected rule hash {applied.get('rule_hash')!r}")
    results = applied["results"]
    if any(not row.get("valid_output") or row.get("error") is not None for row in results):
        raise AssertionError("Racket application failure")
    outputs = [row["output"] for row in results]
    parity = [ud_complete(grid) == output for grid, output in zip(grids, outputs)]
    if not all(parity):
        raise AssertionError("independent Python mirror disagrees with Racket")

    pairs = [{"input": grid, "output": output} for grid, output in zip(grids, outputs)]
    demos, queries = pairs[:DEMO_COUNT], pairs[DEMO_COUNT:]
    rivals = {
        "no_op": lambda grid: deepcopy(grid),
        "left_right_completion": lr_complete,
        "top_to_bottom_only": top_to_bottom_only,
        "bottom_to_top_only": bottom_to_top_only,
        "overwrite_from_top": overwrite_from_top,
    }
    rival_demo_fits = {
        name: [rival(pair["input"]) == pair["output"] for pair in demos]
        for name, rival in rivals.items()
    }
    surviving = sorted(name for name, fits in rival_demo_fits.items() if all(fits))

    def direction(grid):
        h = len(grid)
        top_gap = any(
            grid[r][c] != 0 and grid[h - 1 - r][c] == 0
            for r in range(h // 2)
            for c in range(len(grid[0]))
        )
        bottom_gap = any(
            grid[r][c] != 0 and grid[h - 1 - r][c] == 0
            for r in range((h + 1) // 2, h)
            for c in range(len(grid[0]))
        )
        return {"top_to_bottom_evidence": top_gap, "bottom_to_top_evidence": bottom_gap}

    report.update({
        "status": "completed",
        "generator_version": getattr(gen, "VERSION", None),
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "catalog_rule_hash": applied.get("rule_hash"),
        "racket_labels_checked": len(outputs),
        "python_racket_parity": all(parity),
        "validation_errors": validation,
        "all_inputs_distinct": True,
        "input_shapes": [[len(grid), len(grid[0])] for grid in grids],
        "output_shapes": [[len(output), len(output[0])] for output in outputs],
        "input_sha256": [sha(packed(grid)) for grid in grids],
        "query_output_sha256": [sha(packed(pair["output"])) for pair in queries],
        "demo_direction_evidence": [direction(pair["input"]) for pair in demos],
        "rival_demo_fits": rival_demo_fits,
        "surviving_named_rivals": surviving,
        "four_distinct_queries": len({packed(pair["input"]) for pair in queries}) == QUERY_COUNT,
        "scope": "One deterministic default-setting episode: 3 demonstrations and 4 distinct queries, seven authoritative Racket labels; not an all-seed, all-axis, or throughput result.",
    })
    (OUT / "private_episode.json").write_text(json.dumps({"train": demos, "test": queries}, indent=2) + "\n")
finally:
    report["elapsed_seconds"] = round(time.perf_counter() - started, 6)
    (OUT / "probe_result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report.get("status"),
        "racket_labels_checked": report.get("racket_labels_checked"),
        "python_racket_parity": report.get("python_racket_parity"),
        "surviving_named_rivals": report.get("surviving_named_rivals"),
        "input_shapes": report.get("input_shapes"),
        "elapsed_seconds": report.get("elapsed_seconds"),
    }, indent=2, sort_keys=True))
