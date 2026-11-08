"""Bounded semantic-rival audit for the key-count corner family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("_arc_2e_audit_family", HERE / "family.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load family.py")
family = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(family)


def rival_output(grid, name):
    info = family.analyze(grid)
    count = info["key_count"]
    if name in family.CORNERS:
        return family.output_for_corner(grid, name)
    if name == "reversed_count":
        return family.output_for_corner(grid, family.CORNERS[4 - count])
    if name == "off_by_one":
        return family.output_for_corner(grid, family.CORNERS[count % 4])
    if name == "key_bbox_area":
        top, left, bottom, right = family._bbox(info["key_cells"])
        area = (bottom - top + 1) * (right - left + 1)
        return family.output_for_corner(grid, family.CORNERS[min(4, area) - 1])
    if name == "selected_but_color_2":
        return family.output_for_corner(grid, info["selected_corner"], color=2)
    raise ValueError(name)


def audit(seed=0, demos=3, queries=4):
    rivals = (
        "top_left", "top_right", "bottom_left", "bottom_right",
        "reversed_count", "off_by_one", "key_bbox_area", "selected_but_color_2",
    )
    episode = family.generate(seed, {"anchor_policy": "key_count_corner"}, demos, queries)
    results = {}
    for name in rivals:
        fits = all(rival_output(pair["input"], name) == pair["output"] for pair in episode["train"])
        disagreements = [
            index for index, pair in enumerate(episode["test"])
            if rival_output(pair["input"], name) != pair["output"]
        ]
        results[name] = {"fits_all_demos": fits, "query_disagreements": disagreements}
    return {
        "schema": "arcpuzzles-bounded-parametric-self-audit-v1",
        "task_id": family.TASK_ID,
        "seed": seed,
        "demos": demos,
        "queries": queries,
        "rivals": results,
        "all_rivals_refuted_by_demos": all(not row["fits_all_demos"] for row in results.values()),
        "finite_scope": "Named rivals and sampled scenes only; not a uniqueness proof.",
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
