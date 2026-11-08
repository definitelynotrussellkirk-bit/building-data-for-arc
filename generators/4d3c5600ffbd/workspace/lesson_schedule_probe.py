#!/usr/bin/env python3
"""Exhaustive local probe for the five-pair teaching schedule.

This is reviewer tooling, not label authority.  It uses the generator's tested
Python mirror so future authors can cheaply inspect every cyclic lesson start,
every query rotation, and every declared competitor before paying for a full
Racket-backed census.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


TASK_ID = "4d3c5600ffbd"
HOME = Path(__file__).resolve().parents[1]


def load_generator(path: Path):
    spec = importlib.util.spec_from_file_location(f"schedule_probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_probe(generator, *, seed: int, starts: int) -> dict[str, object]:
    rows = []
    totals = {"windows": 0, "rotations": 0, "surviving_rivals": 0, "hook_reasons": 0}
    for band in ("easy", "medium", "hard"):
        for start in range(starts):
            grids = [generator.generate(seed, start + offset, difficulty=band) for offset in range(5)]
            pairs = [{"input": grid, "output": generator.solve_python(grid)} for grid in grids]
            profiles = [generator.observe_overrides(grid)["scene_profile"] for grid in grids]
            window = {"band": band, "start": start, "profiles": profiles, "rotations": []}
            totals["windows"] += 1
            for query_index in range(5):
                demos = pairs[:query_index] + pairs[query_index + 1 :]
                query = pairs[query_index]
                survivors = [
                    name
                    for name, rival in sorted(generator.LESSON_COMPETITORS.items())
                    if all(rival(pair["input"]) == pair["output"] for pair in demos)
                ]
                reasons = generator.lesson_identifiable(demos, query)
                window["rotations"].append(
                    {"query_index": query_index, "surviving_rivals": survivors, "hook_reasons": reasons}
                )
                totals["rotations"] += 1
                totals["surviving_rivals"] += len(survivors)
                totals["hook_reasons"] += len(reasons)
            rows.append(window)
    return {
        "task_id": TASK_ID,
        "seed": seed,
        "starts_per_band": starts,
        "totals": totals,
        "passed": totals["surviving_rivals"] == 0 and totals["hook_reasons"] == 0,
        "windows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path, default=HOME / "generator.py")
    parser.add_argument("--seed", type=int, default=8801)
    parser.add_argument("--starts", type=int, default=10)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_probe(load_generator(args.generator.resolve()), seed=args.seed, starts=args.starts)
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(json.dumps({"passed": report["passed"], **report["totals"]}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
