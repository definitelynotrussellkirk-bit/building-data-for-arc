#!/usr/bin/env python3
"""Enumerate cyclic lessons and query rotations against live declared rivals."""
from __future__ import annotations

import argparse
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

from arcpuzzles import Catalog

TASK = "9de65c6eed00"


def executed_rule_hash(applied):
    """Read the public Catalog.apply field used by current runtimes."""
    return applied["executed_rule_hash"]


def load(path: Path):
    spec = importlib.util.spec_from_file_location("generator_under_probe", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path,
                        default=Path(__file__).resolve().parents[1] / "generator.py")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    gen = load(args.generator)
    period = gen.LESSON_SCHEDULE_PERIOD
    rivals = dict(gen.LESSON_COMPETITORS)
    rows = []
    all_grids = []
    descriptors = []
    for band in ("easy", "medium", "hard"):
        for start in range(period):
            grids = [gen.generate(args.seed, start + offset, difficulty=band)
                     for offset in range(gen.EXAMPLES_NEEDED + 1)]
            descriptors.append((band, start, grids))
            all_grids.extend(grids)
    applied = Catalog().apply(TASK, all_grids, timeout=180)
    if not applied["rule_hash_matches_catalog"] or any(
            not row["valid_output"] or row["error"] is not None for row in applied["results"]):
        raise RuntimeError("Racket labeling failed")
    cursor = 0
    failures = []
    for band, start, grids in descriptors:
        labels = [row["output"] for row in applied["results"][cursor:cursor + len(grids)]]
        cursor += len(grids)
        predictions = {}
        for name, rival in rivals.items():
            values = []
            for grid in grids:
                original = deepcopy(grid)
                value = rival(grid)
                if grid != original:
                    raise RuntimeError(f"rival {name} mutated its input")
                values.append(value)
            predictions[name] = values
        for query in range(len(grids)):
            demos = [index for index in range(len(grids)) if index != query]
            ambiguous = [name for name, values in predictions.items()
                         if all(values[index] == labels[index] for index in demos)
                         and values[query] != labels[query]]
            row = {"band": band, "start": start, "query": query,
                   "ambiguous": ambiguous}
            rows.append(row)
            if ambiguous:
                failures.append(row)
    report = {"schema": "9de65c6eed00-semantic-probe-v1",
              "generator_sha256": __import__("hashlib").sha256(args.generator.read_bytes()).hexdigest(),
              "rule_hash": executed_rule_hash(applied), "seed": args.seed,
              "period": period, "rivals": sorted(rivals), "rotations": rows,
              "failures": failures, "status": "pass" if not failures else "fail"}
    raw = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(raw)
    print(raw, end="")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
