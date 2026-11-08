"""Bounded independent review of color-group distance shortcuts.

Run through the packet's review.py run wrapper. No generator source is edited.
The default source is a frozen, parse-correct pre-teaching-repair snapshot.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sexp(value):
    return "(" + " ".join(map(sexp, value)) + ")" if isinstance(value, list) else str(value)


def rival_program(mode):
    """Exact mean uses integer cross-products, never the DSL's division."""
    sources = ["filter", ["lambda", ["c"], ["and", [">=", ["at", "g", "r", "c"], 1],
                                                   ["<=", ["at", "g", "r", "c"], 8]]], ["range", ["cols", "g"]]]
    members = ["lambda", ["color"], ["filter", ["lambda", ["c"], ["=", ["at", "g", "r", "c"], "color"]], "sources"]]
    distances = ["lambda", ["color"], ["map", ["lambda", ["c"], ["abs", ["-", "c", "axis"]]], ["members", "color"]]]
    colors = ["filter", ["lambda", ["color"], ["not", ["empty?", ["members", "color"]]]], ["range", 1, 9]]
    if mode in ("min_mean", "max_mean"):
        cmp = "<" if mode == "min_mean" else ">"
        better = [cmp,
                  ["*", ["apply", "+", ["distances", "color"]], ["length", ["members", "best"]]],
                  ["*", ["apply", "+", ["distances", "best"]], ["length", ["members", "color"]]]]
    elif mode == "min_outer":
        better = ["<", ["apply", "max", ["distances", "color"]], ["apply", "max", ["distances", "best"]]]
    elif mode == "max_inner":
        better = [">", ["apply", "min", ["distances", "color"]], ["apply", "min", ["distances", "best"]]]
    else:
        raise ValueError(mode)
    selected = ["for/fold", [["best", ["first", "colors"]]], [["color", ["in-list", "colors"]]],
                ["if", better, "color", "best"]]
    paint = ["for/fold", [["acc", "out"]], [["c", ["in-list", "sources"]]],
             ["if", ["=", ["at", "g", "r", "c"], "selected"],
              ["set-cell", "acc", "r", ["-", ["*", 2, "axis"], "c"], "selected"], "acc"]]
    body = ["let*", [["axis", ["first", "anchors"]], ["members", members],
                     ["distances", distances], ["colors", colors], ["selected", selected]], paint]
    per_row = ["let*", [["anchors", ["filter", ["lambda", ["c"], ["=", ["at", "g", "r", "c"], 9]], ["range", ["cols", "g"]]]],
                         ["sources", sources]],
               ["if", ["or", ["empty?", "anchors"], ["empty?", "sources"]], "out", body]]
    return sexp(["rule!", ["lambda", ["g"], ["for/fold", [["out", "g"]], [["r", ["in-range", ["rows", "g"]]]], per_row]]])


def independent_rows(grid):
    for r, row in enumerate(grid):
        if 9 not in row:
            continue
        anchor = row.index(9)
        groups = {}
        for c, color in enumerate(row):
            if 1 <= color <= 8:
                groups.setdefault(color, []).append((c, abs(c - anchor)))
        yield r, anchor, groups


def rival_python(grid, mode):
    out = deepcopy(grid)
    for r, anchor, groups in independent_rows(grid):
        def score(color):
            distances = [distance for _, distance in groups[color]]
            return (Fraction(sum(distances), len(distances)) if "mean" in mode
                    else max(distances) if mode == "min_outer" else min(distances))
        selector = min if mode.startswith("min") else max
        chosen = selector(sorted(groups), key=score)
        for c, _ in groups[chosen]:
            out[r][2 * anchor - c] = chosen
    return out


def scene_metrics(pair):
    grid, output = pair["input"], pair["output"]
    h, w = len(grid), len(grid[0])
    changed = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != output[r][c]]
    return {"height": h, "width": w,
            "anchors": sum(color == 9 for row in grid for color in row),
            "colored_sources": sum(1 <= color <= 8 for row in grid for color in row),
            "changed_cells": len(changed),
            "changed_row_count": len({r for r, _ in changed}),
            "changed_quadrants": sorted({(2 if r >= h // 2 else 0) + (1 if c >= w // 2 else 0) for r, c in changed}),
            "input_edge_cells": sum(bool(grid[r][c]) for r in range(h) for c in range(w) if r in (0, h-1) or c in (0, w-1))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=HERE / "source_snapshot_valid/native_family.py")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError("fresh output path required")
    source = args.source.resolve()
    spec = importlib.util.spec_from_file_location("review_extents_native", source)
    family = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(family)
    from arcpuzzles.parametric_worker import _real_evaluator
    apply, identity, bridge = _real_evaluator((Path.cwd() / "shared/runtime").resolve())
    report = {"source": str(source), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "racket": identity, "cases": [], "boundary_checks": [],
              "limits": "Bounded teaching review; no acceptance, export, full battery or universal uniqueness claim."}
    executions = 0
    try:
        for seed, policy, mode in ((0, "nearest_color", "min_mean"),
                                   (0, "nearest_color", "min_outer"),
                                   (0, "farthest_color", "max_inner"),
                                   (1, "farthest_color", "max_mean")):
            settings = {"copy_policy": policy}
            episode = family.generate(seed, settings, demos=2, queries=4)
            intended_program = episode["program_solution"]
            alternate_program = rival_program(mode)
            case = {"seed": seed, "settings": settings, "rival": mode,
                    "program": intended_program, "rival_program": alternate_program,
                    "demos_match": [], "queries_match": [], "train": [], "test": []}
            for split in ("train", "test"):
                for pair_index, pair in enumerate(episode[split]):
                    actual = apply(intended_program, pair["input"])
                    predicted = apply(alternate_program, pair["input"])
                    executions += 2
                    assert actual == pair["output"], (seed, policy, split, pair_index, "native mismatch")
                    assert predicted == rival_python(pair["input"], mode), (seed, policy, split, pair_index, "rival mismatch")
                    same = actual == predicted
                    case["demos_match" if split == "train" else "queries_match"].append(same)
                    case[split].append({"input": pair["input"], "output": actual, "rival_output": predicted})
            case["demo_consistent_query_conflict"] = all(case["demos_match"]) and not all(case["queries_match"])
            report["cases"].append(case)
        for policy in ("all", "nearest_color", "farthest_color"):
            episode = family.generate(0, {"copy_policy": policy}, demos=6, queries=4)
            for split, index in (("train", 2), ("train", 5), ("test", 3)):
                pair = episode[split][index]
                actual = apply(episode["program_solution"], pair["input"])
                executions += 1
                assert actual == pair["output"], (policy, split, index, "boundary mismatch")
                report["boundary_checks"].append({"policy": policy, "split": split, "index": index,
                                                   "racket_equals_python": True, **scene_metrics(pair)})
        report["executions"] = executions
        report["blocker_count"] = sum(case["demo_consistent_query_conflict"] for case in report["cases"])
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({key: report[key] for key in ("source_sha256", "executions", "blocker_count", "boundary_checks")}, indent=2))
        print(str(args.out))
    finally:
        bridge.close()


if __name__ == "__main__":
    main()
