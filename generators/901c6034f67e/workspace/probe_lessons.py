#!/usr/bin/env python3
"""Quick source-bound cyclic-window probe for task 901c6034f67e.

This is a reviewer tool, not a selected generator.  It uses the generator's
actual default sampler and declared LESSON_COMPETITORS; no rival names or
profile expectations are duplicated here.  Racket remains the external label
authority in the battery/census.  This probe exercises the pinned Python mirror
for fast local regression and records the exact generator source hash.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Iterable

TASK_DIR = Path(__file__).resolve().parents[1]
GENERATOR_PATH = TASK_DIR / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "contour_rank_generator_for_probe", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid_key(grid) -> str:
    return json.dumps(grid, separators=(",", ":"))


def run_probe(
    *,
    seed: int = 4242,
    starts: int = 18,
    bands: Iterable[str] = ("easy", "medium", "hard"),
) -> dict:
    """Measure every cyclic 3-demo window across ``starts`` sampler positions."""
    if starts < 1:
        raise ValueError("starts must be positive")
    bands = tuple(bands)
    if not bands or any(band not in ("easy", "medium", "hard") for band in bands):
        raise ValueError("bands must be a nonempty subset of easy, medium, hard")

    gen = _load_generator()
    rivals = dict(gen.LESSON_COMPETITORS)
    report = {
        "schema": "contour-rank-cyclic-probe-v1",
        "task_id": gen.TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "declared_rule_hash": gen.RULE_HASH,
        "seed": seed,
        "starts": starts,
        "lesson_policy": "3 consecutive default samples as demonstrations; fourth as query",
        "rivals": sorted(rivals),
        "bands": {},
        "errors": [],
    }

    for band in bands:
        unique_inputs: set[str] = set()
        profile_counts: Counter[str] = Counter()
        palette_counts: Counter[str] = Counter()
        rival_refuted = Counter({name: 0 for name in rivals})
        rival_query_disagreements = Counter({name: 0 for name in rivals})
        identifiable = 0
        windows = []

        for start in range(starts):
            pairs = []
            observed = []
            for sample_index in range(start, start + 4):
                grid = gen.generate(seed, sample_index, difficulty=band)
                output = gen.rule_mirror(grid)
                pairs.append({"input": grid, "output": output})
                unique_inputs.add(_grid_key(grid))
                axes = gen.observe_overrides(grid)
                observed.append(axes)
                profile_counts[axes["scene_profile"]] += 1
                palette_counts[axes["palette_mode"]] += 1

            demos, query = pairs[:3], pairs[3]
            reasons = gen.lesson_identifiable(demos, query)
            if not reasons:
                identifiable += 1
            else:
                report["errors"].append(
                    {"band": band, "start": start, "reasons": reasons}
                )

            refuted_here = []
            query_disagrees_here = []
            for name, rival in rivals.items():
                if any(rival(pair["input"]) != pair["output"] for pair in demos):
                    rival_refuted[name] += 1
                    refuted_here.append(name)
                if rival(query["input"]) != query["output"]:
                    rival_query_disagreements[name] += 1
                    query_disagrees_here.append(name)

            windows.append(
                {
                    "start": start,
                    "sample_indices": list(range(start, start + 4)),
                    "demo_axes": observed[:3],
                    "query_axes": observed[3],
                    "identifiable": not reasons,
                    "refuted_in_demos": sorted(refuted_here),
                    "query_disagreements": sorted(query_disagrees_here),
                }
            )

        report["bands"][band] = {
            "windows": starts,
            "identifiable_windows": identifiable,
            "unique_inputs": len(unique_inputs),
            "profile_counts": dict(sorted(profile_counts.items())),
            "palette_counts": dict(sorted(palette_counts.items())),
            "rival_refuted_windows": dict(sorted(rival_refuted.items())),
            "rival_query_disagreement_windows": dict(
                sorted(rival_query_disagreements.items())
            ),
            "window_records": windows,
        }

    report["all_windows_identifiable"] = not report["errors"] and all(
        band["identifiable_windows"] == band["windows"]
        and all(count == band["windows"] for count in band["rival_refuted_windows"].values())
        for band in report["bands"].values()
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=4242)
    parser.add_argument("--starts", type=int, default=18)
    parser.add_argument(
        "--bands", default="easy,medium,hard",
        help="comma-separated subset of easy,medium,hard",
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_probe(
        seed=args.seed,
        starts=args.starts,
        bands=tuple(part.strip() for part in args.bands.split(",") if part.strip()),
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    return 0 if report["all_windows_identifiable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
