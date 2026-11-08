#!/usr/bin/env python3
"""Bounded authoring audit for the native 43cca8eff94f parametric family.

This tool deliberately stays independent of qualification: it exercises Python
construction invariants and a finite set of plausible rival rules. The owner
qualification remains the authority for protected-Racket execution.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK_ID = "43cca8eff94f"
HOME = Path(__file__).resolve().parent
REPO = HOME.parents[3]
ADAPTER_PATH = HOME / "adapter.py"
CANONICAL_PATH = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"


def _load_adapter():
    name = "_arc_parametric_probe_43cca8eff94f"
    spec = importlib.util.spec_from_file_location(name, ADAPTER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load adapter: {ADAPTER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = set()
    with CANONICAL_PATH.open(encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and row.get("program_solution"):
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise RuntimeError(f"expected one selected canonical program, found {len(programs)}")
    return next(iter(programs))


def _exact_int(name: str, value: object, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in [{low}, {high}]")
    return value


def _normalized_seeds(seeds) -> list[int]:
    if type(seeds) not in (list, tuple) or not 1 <= len(seeds) <= 64:
        raise ValueError("seeds must be a nonempty list/tuple of at most 64 values")
    normalized = [_exact_int("seed", seed, 0, 2**63 - 1) for seed in seeds]
    if len(normalized) != len(set(normalized)):
        raise ValueError("seeds must be distinct")
    return normalized


def _pairs(episode):
    return episode["train"] + episode["test"]


def _inputs(episode):
    return [pair["input"] for pair in _pairs(episode)]


def _grid_key(grid) -> str:
    return json.dumps(grid, separators=(",", ":"))


def _same_prefix(adapter, seed: int, setting: dict, demos: int, queries: int) -> bool:
    full = adapter.generate(seed, deepcopy(setting), demos=demos, queries=queries)
    minimum = adapter.generate(seed, deepcopy(setting), demos=2, queries=1)
    middle = adapter.generate(seed, deepcopy(setting), demos=min(3, demos), queries=min(2, queries))
    return (
        minimum["train"] == full["train"][:2]
        and minimum["test"] == full["test"][:1]
        and middle["train"] == full["train"][: min(3, demos)]
        and middle["test"] == full["test"][: min(2, queries)]
    )


def build_report(*, seeds=(0, 17, 91), demos=6, queries=4) -> dict:
    """Return a JSON-safe audit report over a bounded seed/rival set."""
    normalized_seeds = _normalized_seeds(seeds)
    demos = _exact_int("demos", demos, 2, 6)
    queries = _exact_int("queries", queries, 1, 4)
    adapter = _load_adapter()
    settings = [{"finish": finish} for finish in adapter.FINISHES]
    if settings != [{"finish": "dock_only"}, {"finish": "contact_projection"}]:
        raise RuntimeError("unexpected setting inventory")

    canonical = _canonical_program()
    checks = {
        "canonical_program_exact": adapter.program(settings[0]).encode() == canonical.encode(),
        "deterministic": True,
        "count_prefix_invariant": True,
        "same_inputs_across_settings": True,
        "every_demo_identifies_setting": True,
        "contact_projection_refutes_bbox_span": True,
        "contact_projection_refutes_wrong_order": True,
        "contains_30x30_query": True,
        "covers_all_cardinal_directions": True,
    }
    episodes = []
    for seed in normalized_seeds:
        generated = {
            setting["finish"]: adapter.generate(seed, deepcopy(setting), demos=demos, queries=queries)
            for setting in settings
        }
        repeated = {
            setting["finish"]: adapter.generate(seed, deepcopy(setting), demos=demos, queries=queries)
            for setting in settings
        }
        checks["deterministic"] &= generated == repeated
        checks["count_prefix_invariant"] &= all(
            _same_prefix(adapter, seed, setting, demos, queries) for setting in settings
        )
        dock = generated["dock_only"]
        projected = generated["contact_projection"]
        dock_inputs = [_grid_key(grid) for grid in _inputs(dock)]
        projected_inputs = [_grid_key(grid) for grid in _inputs(projected)]
        checks["same_inputs_across_settings"] &= dock_inputs == projected_inputs
        demo_separations = sum(
            left["output"] != right["output"]
            for left, right in zip(dock["train"], projected["train"])
        )
        checks["every_demo_identifies_setting"] &= demo_separations == demos

        facts = [adapter.dock_intermediate(pair["input"]) for pair in _pairs(projected)]
        bbox_mismatches = sum(
            adapter.bbox_projection_solve(pair["input"]) != pair["output"]
            for pair in _pairs(projected)
        )
        wrong_order_mismatches = sum(
            adapter.wrong_order_solve(pair["input"]) != pair["output"]
            for pair in _pairs(projected)
        )
        case_count = demos + queries
        checks["contact_projection_refutes_bbox_span"] &= bbox_mismatches == case_count
        checks["contact_projection_refutes_wrong_order"] &= wrong_order_mismatches == case_count
        query_shapes = [[len(pair["input"]), len(pair["input"][0])] for pair in projected["test"]]
        checks["contains_30x30_query"] &= [30, 30] in query_shapes
        directions = sorted({fact["direction"] for fact in facts})
        checks["covers_all_cardinal_directions"] &= directions == ["down", "left", "right", "up"]
        episodes.append({
            "seed": seed,
            "demo_separations": demo_separations,
            "bbox_mismatches": bbox_mismatches,
            "wrong_order_mismatches": wrong_order_mismatches,
            "directions": directions,
            "query_shapes": query_shapes,
            "contact_count_range": [
                min(len(fact["contact_cells"]) for fact in facts),
                max(len(fact["contact_cells"]) for fact in facts),
            ],
            "projection_count_range": [
                min(len(fact["projection_cells"]) for fact in facts),
                max(len(fact["projection_cells"]) for fact in facts),
            ],
            "distinct_visible_inputs": len(set(projected_inputs)),
        })

    return {
        "schema": "arcpuzzles-parametric-authoring-probe-v1",
        "task_id": TASK_ID,
        "seeds": normalized_seeds,
        "counts": {"demos": demos, "queries": queries,
                   "cases": len(normalized_seeds) * (demos + queries)},
        "settings": settings,
        "program_sha256": {
            setting["finish"]: hashlib.sha256(adapter.program(setting).encode()).hexdigest()
            for setting in settings
        },
        "finite_rivals": [
            {
                "name": "other_admitted_setting",
                "claim": "The canonical docking-only output also explains projected episodes.",
                "refutation": "Every generated demonstration changes under contact_projection.",
            },
            {
                "name": "bbox_span_projection",
                "claim": "Project the full docked red bounding-box span rather than sparse contacts.",
                "refutation": "Comb profiles contain a deliberately missing leading-edge contact.",
            },
            {
                "name": "project_before_dock",
                "claim": "Run projection before the rigid slide.",
                "refutation": "Every source has a positive gap, so pre-dock contact seeds are empty.",
            },
        ],
        "checks": checks,
        "episodes": episodes,
        "limits": (
            "This is a bounded Python authoring audit over the listed seeds and rivals. "
            "Protected-Racket labels and finite-setting identification require native qualification."
        ),
    }


def write_report(path, report: dict) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return target


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", action="append", type=int, dest="seeds",
                        help="bounded audit seed; repeatable (default: 0,17,91)")
    parser.add_argument("--demos", type=int, default=6)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = build_report(seeds=args.seeds or [0, 17, 91], demos=args.demos, queries=args.queries)
    if args.out:
        write_report(args.out, report)
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 0 if all(report["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
