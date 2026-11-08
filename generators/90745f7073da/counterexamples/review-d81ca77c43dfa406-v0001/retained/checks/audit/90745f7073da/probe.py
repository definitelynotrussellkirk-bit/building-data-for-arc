#!/usr/bin/env python3
"""Find/replay one source-bound payload placement witness; no source mutations."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
SOURCE = REPO / "generators/90745f7073da/generator.py"
sys.path.insert(0, str(REPO / "shared/runtime"))


def dump(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def positions(grid, color):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]


def outputs(grid):
    h, w = len(grid), len(grid[0])
    p1, p2 = positions(grid, 1)[0], positions(grid, 2)[0]
    dr, dc = p2[0] - p1[0], p2[1] - p1[1]
    translated = [(r + dr, c + dc) for r, c in positions(grid, 4)]
    survivors = [(r, c) for r, c in translated if 0 <= r < h and 0 <= c < w]
    dropped = [(r, c) for r, c in translated if not (0 <= r < h and 0 <= c < w)]
    exact = [[0] * w for _ in range(h)]
    if survivors:
        for r in range(min(r for r, _ in survivors), max(r for r, _ in survivors) + 1):
            for c in range(min(c for _, c in survivors), max(c for _, c in survivors) + 1):
                exact[r][c] = 4
    rival = [[0] * w for _ in range(h)] if dropped else exact
    return {
        "markers": {"color_1": p1, "color_2": p2},
        "vector": [dr, dc],
        "payload_cells": positions(grid, 4),
        "translated_cells": translated,
        "surviving_cells": survivors,
        "dropped_cells": dropped,
        "python_authority_mirror": exact,
        "python_rival_output": rival,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int)
    parser.add_argument("--search-seeds", type=int, default=32)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("audited_generator_90745f7073da", SOURCE)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    examined = []
    seeds = [args.seed] if args.seed is not None else range(args.search_seeds)
    for seed in seeds:
        trace_data = {}

        def trace(frame, event, arg):
            if frame.f_code.co_filename == str(SOURCE) and frame.f_code.co_name == "generate" and event == "return":
                for key in ("h", "w", "dr", "dc", "shape", "sh", "sw", "r_lo", "r_hi", "c_lo", "c_hi", "r0", "c0", "cells"):
                    if key in frame.f_locals:
                        value = frame.f_locals[key]
                        trace_data[key] = sorted(value) if isinstance(value, set) else value
            return trace

        sys.settrace(trace)
        try:
            grid = generator.generate(seed, 0, difficulty=None)
        finally:
            sys.settrace(None)
        result = outputs(grid)
        errors = generator.self_check(grid, difficulty=None, meta={})
        examined.append({"seed": seed, "sample_index": 0, "difficulty": None, "overrides": {}, "self_check_errors": errors, "dropped_count": len(result["dropped_cells"])})
        if not result["dropped_cells"]:
            continue
        canonical = json.loads((HERE / "canonical.json").read_text())
        evidence = {
            "task_id": generator.TASK_ID,
            "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            "rule_hash": canonical["rule_hash"],
            "seed": seed,
            "sample_index": 0,
            "difficulty": None,
            "overrides": {},
            "input": grid,
            "self_check_errors": errors,
            "validator_accepts": errors == [],
            "documented_domain_status": "outside documented invariant: at least one actual grid payload cell leaves the grid after translation",
            "actual_generation_status": "unmodified generate(seed, 0, difficulty=None), with no overrides",
            "trace": trace_data,
            "rival_description": "If any translated payload cell leaves the grid, discard the whole payload; otherwise translate and fill its bounding box.",
            "rival_intent": "intentional diagnostic rival; this is not a blind solve",
            **result,
            "examined": examined,
        }
        dump("input.json", grid)
        dump("python-rival.json", result["python_rival_output"])
        dump("python-authority-mirror.json", result["python_authority_mirror"])
        dump("probe-result.json", evidence)
        print(json.dumps({"source_sha256": evidence["source_sha256"], "rule_hash": evidence["rule_hash"], "seed": seed, "examined": len(examined), "dimensions": [len(grid), len(grid[0])], "vector": result["vector"], "dropped_cells": result["dropped_cells"], "surviving_cells": result["surviving_cells"], "self_check_errors": errors, "trace": trace_data}, sort_keys=True))
        return 0
    dump("probe-search.json", examined)
    print("No clipping witness found in the stated seed range.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
