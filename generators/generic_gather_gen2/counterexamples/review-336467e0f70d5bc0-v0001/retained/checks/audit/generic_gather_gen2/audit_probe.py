#!/usr/bin/env python3
"""Adversarial teaching probe for generic_gather_gen2.

Searches deterministic seed ranges for plausible rivals that fit every training
pair but disagree on at least one query.  It also measures whether the optional
recolor branch is actually demonstrated and exercised by the query.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve()
PACKET = HERE.parents[3]
REPO = PACKET / "repo"
RUNTIME = REPO / "shared" / "runtime"
GENERATOR = REPO / "generators" / "generic_gather_gen2" / "generator.py"
sys.path.insert(0, str(RUNTIME))


def load_module():
    spec = importlib.util.spec_from_file_location("audit_generic_gather_gen2", GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {GENERATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def contains(grid, color):
    return any(value == color for row in grid for value in row)


def no_recolor(module, grid, params):
    rival = dict(params)
    rival["recolor"] = None
    return module._apply(grid, rival)


def reverse_order(module, grid, params):
    rival = dict(params)
    rival["dir1"], rival["dir2"] = rival["dir2"], rival["dir1"]
    return module._apply(grid, rival)


def only(module, grid, params, which):
    out = grid
    if params["recolor"] is not None:
        out = module._recolor(out, *params["recolor"])
    return module._gravity(out, params[which], params["bg"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds-per-band", type=int, default=10_000)
    parser.add_argument("--full-rival-seeds-per-band", type=int, default=200)
    parser.add_argument("--bands", default="easy,medium,hard")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    module = load_module()
    counts = Counter()
    first = {}
    bands = tuple(part.strip() for part in args.bands.split(",") if part.strip())
    if not bands or any(b not in {"easy", "medium", "hard"} for b in bands):
        raise ValueError("--bands must be a comma-separated subset of easy,medium,hard")
    rivals = {
        "omit_recolor": lambda g, p: no_recolor(module, g, p),
        "reverse_gravity_order": lambda g, p: reverse_order(module, g, p),
        "only_first_gravity": lambda g, p: only(module, g, p, "dir1"),
        "only_second_gravity": lambda g, p: only(module, g, p, "dir2"),
    }

    for band in bands:
        for seed in range(args.seeds_per_band):
            counts["tasks"] += 1
            task = module.generate_task(seed, difficulty=band)
            params = module._params_from_program(task["program"])
            if seed < min(100, args.full_rival_seeds_per_band):
                counts["self_check_tasks"] += 1
                errors = list(module.self_check_task(task) or [])
                if errors:
                    counts["self_check_failures"] += 1
                    first.setdefault("self_check_failure", {"band": band, "seed": seed, "errors": errors})
            if seed < min(100, args.full_rival_seeds_per_band):
                pairs = task["train"] + task["test"]
                fingerprints = [hashlib.sha256(json.dumps(pair, sort_keys=True).encode()).hexdigest() for pair in pairs]
                if len(fingerprints) != len(set(fingerprints)):
                    counts["tasks_with_duplicate_pairs"] += 1

            if params["recolor"] is not None:
                counts["recolor_tasks"] += 1
                src, dst = params["recolor"]
                train_presence = [contains(pair["input"], src) for pair in task["train"]]
                test_presence = [contains(pair["input"], src) for pair in task["test"]]
                if not any(train_presence):
                    counts["recolor_source_absent_all_train"] += 1
                if not any(test_presence):
                    counts["recolor_source_absent_all_test"] += 1
                if not any(train_presence) and any(test_presence):
                    counts["recolor_untaught_but_query_active"] += 1
                if all(train_presence):
                    counts["recolor_source_present_every_train"] += 1
                if all(test_presence):
                    counts["recolor_source_present_every_test"] += 1
                if any(contains(pair["input"], dst) for pair in task["train"]):
                    counts["recolor_destination_already_present_in_train"] += 1

            # Omit-recolor is cheap to classify from source-color presence:
            # when src is absent in every demo, the rival is exactly equal there.
            # Evaluate outputs only on the query, where a source cell may occur.
            candidate_names = ["omit_recolor"] if params["recolor"] is not None else []
            if seed < args.full_rival_seeds_per_band:
                candidate_names.extend(["reverse_gravity_order", "only_first_gravity", "only_second_gravity"])
            for name in candidate_names:
                rival = rivals[name]
                if name == "omit_recolor" and params["recolor"] is not None:
                    src = params["recolor"][0]
                    train_fits = not any(contains(pair["input"], src) for pair in task["train"])
                else:
                    train_fits = all(rival(pair["input"], params) == pair["output"] for pair in task["train"])
                if not train_fits:
                    continue
                counts[f"{name}_fits_train"] += 1
                flags = [rival(pair["input"], params) != pair["output"] for pair in task["test"]]
                if any(flags):
                    counts[f"{name}_fits_train_differs_test"] += 1
                    first.setdefault(
                        name,
                        {
                            "band": band,
                            "seed": seed,
                            "program": task["program"],
                            "test_difference_flags": flags,
                            "train_count": len(task["train"]),
                            "test_count": len(task["test"]),
                        },
                    )
                else:
                    counts[f"{name}_fits_entire_task"] += 1

    report = {
        "schema": "generic-gather-gen2-audit-probe/1",
        "task_id": "generic_gather_gen2",
        "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
        "version": module.VERSION,
        "bands": list(bands),
        "seed_range_per_band": [0, args.seeds_per_band - 1],
        "full_rival_seed_range_per_band": [0, args.full_rival_seeds_per_band - 1],
        "counts": dict(sorted(counts.items())),
        "first_findings": first,
        "limits": [
            "Finite search over four declared plausible rivals; not a proof of universal identifiability.",
            "generate_task chooses 3..4 training and 1..2 test pairs internally; the supported CLI may expose a requested subset.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"tasks": counts["tasks"], "finding": first.get("omit_recolor"), "counts": dict(counts)}, sort_keys=True))
    return 1 if counts["omit_recolor_fits_train_differs_test"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
