"""Bounded semantic-rival audit for the key-selected-row family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("_arc_2a_audit_family", HERE / "family.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load family.py")
family = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(family)


def _fill_one(grid, row_index):
    out = [row[:] for row in grid]
    family._fill_row(out, grid, row_index)
    return out


def rival_output(grid, name):
    info = family.analyze(grid)
    rows = info["payload_rows"]
    if name == "canonical_all":
        return family.canonical_output(grid)
    if name == "always_first":
        return _fill_one(grid, rows[0])
    if name == "always_last":
        return _fill_one(grid, rows[-1])
    if name == "off_by_one":
        return _fill_one(grid, rows[min(len(rows) - 1, info["selector_rank"])])
    if name == "largest_gap":
        chosen = max(rows, key=lambda r: family._row_nonzero(grid[r])[1][0] - family._row_nonzero(grid[r])[0][0])
        return _fill_one(grid, chosen)
    if name == "smallest_gap":
        chosen = min(rows, key=lambda r: family._row_nonzero(grid[r])[1][0] - family._row_nonzero(grid[r])[0][0])
        return _fill_one(grid, chosen)
    if name == "highest_color":
        chosen = max(rows, key=lambda r: family._row_nonzero(grid[r])[0][1])
        return _fill_one(grid, chosen)
    raise ValueError(name)


def audit(seed=0, demos=3, queries=4):
    rivals = ("canonical_all", "always_first", "always_last", "off_by_one", "largest_gap", "smallest_gap", "highest_color")
    episode = family.generate(seed, {"fill_scope": "key_selected"}, demos, queries)
    train = episode["train"]
    test = episode["test"]
    results = {}
    for name in rivals:
        fits = all(rival_output(pair["input"], name) == pair["output"] for pair in train)
        disagrees = [i for i, pair in enumerate(test) if rival_output(pair["input"], name) != pair["output"]]
        results[name] = {"fits_all_demos": fits, "query_disagreements": disagrees}
    return {
        "schema": "arcpuzzles-bounded-parametric-self-audit-v1",
        "task_id": family.TASK_ID,
        "seed": seed,
        "demos": demos,
        "queries": queries,
        "rivals": results,
        "all_rivals_refuted_by_demos": all(not row["fits_all_demos"] for row in results.values()),
        "finite_scope": "Named rivals and sampled scenes only; not a uniqueness proof."
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = audit(args.seed, args.demos, args.queries)
    raw = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(raw)
    print(raw, end="")


if __name__ == "__main__":
    main()
