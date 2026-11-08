#!/usr/bin/env python3
"""Exhaustively probe every deterministic schedule start and query rotation.

This extends the shared census's one-fixed-seed schedule enumeration across a
bounded seed range.  It dynamically consumes LESSON_COMPETITORS so future
reviewers do not need to duplicate a rival-name list when the generator evolves.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Iterable


def _grid_copy(grid):
    return [list(row) for row in grid]


def _pair_copy(pair):
    return {"input": _grid_copy(pair["input"]), "output": _grid_copy(pair["output"])}


def probe_generator(module, *, seeds: Iterable[int], bands: Iterable[str]):
    period = int(module.LESSON_SCHEDULE_PERIOD)
    demo_count = int(module.EXAMPLES_NEEDED)
    bundle_size = demo_count + 1
    rivals = dict(module.LESSON_COMPETITORS)
    starts = list(range(period))
    seed_values = [int(seed) for seed in seeds]
    band_values = [str(band) for band in bands]

    summary = {
        "lessons": 0,
        "rotations": 0,
        "ambiguous_rotations": 0,
        "hook_warnings": 0,
        "scoring_errors": 0,
    }
    rival_stats = {
        name: {"demo_survivals": 0, "ambiguous_rotations": 0, "errors": 0}
        for name in rivals
    }
    examples = {"ambiguity": None, "hook_warning": None, "scoring_error": None}

    for band in band_values:
        for seed in seed_values:
            for start in starts:
                pairs = []
                for offset in range(bundle_size):
                    sample_index = start + offset
                    grid = module.generate(seed, sample_index, difficulty=band)
                    pairs.append({"input": grid, "output": module.rule_mirror(grid)})
                summary["lessons"] += 1

                for query_index, query in enumerate(pairs):
                    demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                    summary["rotations"] += 1
                    try:
                        reasons = module.lesson_identifiable(
                            [_pair_copy(pair) for pair in demos], _pair_copy(query)
                        )
                    except Exception as exc:  # fail loud in the report, not by truncating it
                        reasons = [f"lesson_identifiable raised {type(exc).__name__}: {exc}"]
                    if reasons:
                        summary["hook_warnings"] += 1
                        if examples["hook_warning"] is None:
                            examples["hook_warning"] = {
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "query_index": query_index,
                                "reasons": list(reasons),
                                "pairs": deepcopy(pairs),
                            }

                    for name, rival in rivals.items():
                        try:
                            survives = all(
                                rival(_grid_copy(pair["input"])) == pair["output"]
                                for pair in demos
                            )
                            if survives:
                                rival_stats[name]["demo_survivals"] += 1
                            differs = rival(_grid_copy(query["input"])) != query["output"]
                        except Exception as exc:
                            summary["scoring_errors"] += 1
                            rival_stats[name]["errors"] += 1
                            if examples["scoring_error"] is None:
                                examples["scoring_error"] = {
                                    "band": band,
                                    "seed": seed,
                                    "start": start,
                                    "query_index": query_index,
                                    "rival": name,
                                    "error": f"{type(exc).__name__}: {exc}",
                                }
                            continue
                        if survives and differs:
                            summary["ambiguous_rotations"] += 1
                            rival_stats[name]["ambiguous_rotations"] += 1
                            if examples["ambiguity"] is None:
                                examples["ambiguity"] = {
                                    "band": band,
                                    "seed": seed,
                                    "start": start,
                                    "query_index": query_index,
                                    "rival": name,
                                    "pairs": deepcopy(pairs),
                                }

    source = Path(module.__file__).resolve()
    status = (
        "no_ambiguity_found"
        if not summary["ambiguous_rotations"]
        and not summary["hook_warnings"]
        and not summary["scoring_errors"]
        else "findings"
    )
    return {
        "schema": "arc-task-cyclic-lesson-probe-v1",
        "task_id": module.TASK_ID,
        "status": status,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "rule_hash": module.RULE_HASH,
        "examples_needed": demo_count,
        "bundle_size": bundle_size,
        "schedule_period": period,
        "schedule_starts": starts,
        "seeds": seed_values,
        "bands": band_values,
        "summary": summary,
        "rivals": rival_stats,
        "examples": examples,
    }


def _load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("task_generator_for_cyclic_probe", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path, default=Path(__file__).resolve().parents[1] / "generator.py")
    parser.add_argument("--seed-start", type=int, default=730000)
    parser.add_argument("--seed-count", type=int, default=25)
    parser.add_argument("--bands", default="easy,medium,hard")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.seed_count < 1:
        parser.error("--seed-count must be positive")
    bands = tuple(item.strip() for item in args.bands.split(",") if item.strip())
    if not bands:
        parser.error("--bands must name at least one band")

    module = _load_generator(args.generator.resolve())
    report = probe_generator(
        module,
        seeds=range(args.seed_start, args.seed_start + args.seed_count),
        bands=bands,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], **report["summary"]}, indent=2))
    return 0 if report["status"] == "no_ambiguity_found" else 1


if __name__ == "__main__":
    raise SystemExit(main())
