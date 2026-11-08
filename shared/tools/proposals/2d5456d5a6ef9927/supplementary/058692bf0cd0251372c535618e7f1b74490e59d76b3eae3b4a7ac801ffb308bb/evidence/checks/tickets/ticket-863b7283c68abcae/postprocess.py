#!/usr/bin/env python3
"""Deterministic, no-Racket postprocess for the bounded allocation probe.

This replays the exact seven inputs from allocation_probe.py and evaluates
simple alternative rules against the three demonstration labels produced by
an independent Python mirror.  It deliberately does not call Catalog.apply,
so the ticket's one authoritative runtime probe remains exactly one call.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import find_root

TASK_ID = "9e204e7ff3a2"
TICKET_ID = "ticket-863b7283c68abcae"
TICKET_SEED = "20e22b8b9d86938f5432d86d1c9f34ad9984754609ab5521d0d3222e835b01c4"
SEED = int(TICKET_SEED[:16], 16)
DEMO_COUNT = 3
QUERY_COUNT = 4
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
GEN_PATH = ROOT / "generators" / TASK_ID / "generator.py"


def _sha(value) -> str:
    if isinstance(value, bytes):
        raw = value
    else:
        raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _load_generator():
    spec = importlib.util.spec_from_file_location("allocation_target_postprocess", GEN_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def direction_evidence(grid):
    h = len(grid)
    top_to_bottom = any(
        grid[r][c] != 0 and grid[h - 1 - r][c] == 0
        for r in range(h // 2)
        for c in range(len(grid[0]))
    )
    bottom_to_top = any(
        grid[r][c] != 0 and grid[h - 1 - r][c] == 0
        for r in range((h + 1) // 2, h)
        for c in range(len(grid[0]))
    )
    return {
        "top_to_bottom_evidence": top_to_bottom,
        "bottom_to_top_evidence": bottom_to_top,
    }


def main() -> None:
    gen = _load_generator()
    grids = [gen.generate(SEED, i, difficulty=None) for i in range(DEMO_COUNT + QUERY_COUNT)]
    validation = [gen.self_check(grid) for grid in grids]
    assert not any(validation), validation
    hashes = [_sha(grid) for grid in grids]
    assert len(set(hashes)) == len(hashes), "episode contains duplicate inputs"

    outputs = [ud_complete(grid) for grid in grids]
    demos = list(zip(grids[:DEMO_COUNT], outputs[:DEMO_COUNT]))
    rivals = {
        "no_op": lambda grid: deepcopy(grid),
        "left_right_completion": lr_complete,
        "top_to_bottom_only": top_to_bottom_only,
        "bottom_to_top_only": bottom_to_top_only,
        "overwrite_from_top": overwrite_from_top,
    }
    rival_demo_fits = {
        name: [fn(grid) == output for grid, output in demos]
        for name, fn in rivals.items()
    }
    surviving = sorted(name for name, fits in rival_demo_fits.items() if all(fits))

    result = {
        "schema": "allocation-quality-postprocess-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "ticket_seed": TICKET_SEED,
        "episode_seed": SEED,
        "generator_version": getattr(gen, "VERSION", None),
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "source_sha256": _sha(GEN_PATH.read_bytes()),
        "demo_count": DEMO_COUNT,
        "query_count": QUERY_COUNT,
        "authoritative_runtime_calls": 0,
        "labels_basis": "independent Python mirror only; the separate one-call probe reached Catalog.apply but stopped on receipt-schema mismatch before retaining labels",
        "query_answers_used_for_rival_elimination": False,
        "validation_errors": validation,
        "all_inputs_distinct": True,
        "input_shapes": [[len(grid), len(grid[0])] for grid in grids],
        "input_sha256": hashes,
        "demo_direction_evidence": [direction_evidence(grid) for grid, _ in demos],
        "rival_demo_fits": rival_demo_fits,
        "surviving_named_rivals": surviving,
        "four_distinct_queries": len(set(hashes[DEMO_COUNT:])) == QUERY_COUNT,
        "visible_rule_effect_in_all_inputs": all(ud_complete(grid) != grid for grid in grids),
        "scope": "Exact replay of one deterministic default-setting 3-demo/4-query episode; no Racket call, no all-axis claim, no throughput claim.",
    }
    out_path = HERE / "postprocess.json"
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(out_path),
        "all_inputs_distinct": result["all_inputs_distinct"],
        "input_shapes": result["input_shapes"],
        "surviving_named_rivals": surviving,
        "visible_rule_effect_in_all_inputs": result["visible_rule_effect_in_all_inputs"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
