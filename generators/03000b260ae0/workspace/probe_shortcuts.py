#!/usr/bin/env python3
"""Materialize deterministic declared-rival witnesses for 03000b260ae0.

This authoring probe does not execute the Racket authority. Pair its ``input.json``
with ``python -m arcpuzzles apply`` and compare that output to the saved rival.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "03000b260ae0"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--sample-index", type=int, default=0)
    args = parser.parse_args()

    root = find_root(__file__)
    gen, source, digest = load_selected_generator(TASK_ID, root=root)
    overrides = {"grid_h": 8, "grid_w": 10, "overlap": "double", "texture": "multicolor", "n_markers": 2}
    grid = gen.generate(args.seed, args.sample_index, **overrides)
    rival = gen.SEMANTIC_RIVALS["binary_union"](grid)
    intended_mirror = gen._rule_count_map(grid)
    payload = {
        "schema": "arcpuzzles-shortcut-counterexample-v1",
        "task_id": TASK_ID,
        "generator_path": str(source.relative_to(root)),
        "generator_sha256": digest,
        "rule_hash": gen.RULE_HASH,
        "seed": args.seed,
        "sample_index": args.sample_index,
        "difficulty": None,
        "overrides": overrides,
        "observed_axes": gen.observe_overrides(grid),
        "self_check": gen.self_check(grid),
        "witnesses": {name: bool(fn(grid)) for name, fn in gen.SEMANTIC_WITNESSES.items()},
        "input": grid,
        "python_intended_mirror": intended_mirror,
        "rival_name": "binary_union",
        "rival_output": rival,
        "outputs_differ": intended_mirror != rival,
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "input.json").write_text(json.dumps(grid, indent=2) + "\n", encoding="utf-8")
    (out_dir / "probe.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out_dir": str(out_dir), "generator_sha256": digest,
                      "outputs_differ": payload["outputs_differ"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
