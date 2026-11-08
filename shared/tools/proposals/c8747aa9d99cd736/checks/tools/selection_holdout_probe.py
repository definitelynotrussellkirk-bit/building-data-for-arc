#!/usr/bin/env python3
"""Portable preflight for cyclic lessons with declared selection rivals.

This tool intentionally uses a task's Python rule mirror.  It is fast authoring
feedback, not a replacement for the Racket-backed semantic gate/census.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


def find_repo(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "generators").is_dir() and (candidate / "shared").is_dir():
            return candidate
        if (candidate / "repo/generators").is_dir():
            return candidate / "repo"
    raise RuntimeError(f"could not locate repo from {start}")


def load_generator(repo: Path, task_id: str) -> tuple[ModuleType, Path]:
    runtime = repo / "shared/runtime"
    sys.path.insert(0, str(runtime))
    path = repo / "generators" / task_id / "generator.py"
    if not path.is_file():
        raise FileNotFoundError(path)
    name = f"selection_probe_{task_id}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module, path


def pair(gen: ModuleType, grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_id")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--bands", default="easy,medium,hard")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--require-two-refutations", action="store_true")
    args = parser.parse_args()

    repo = find_repo(Path(__file__).resolve())
    gen, source = load_generator(repo, args.task_id)
    competitors = getattr(gen, "LESSON_COMPETITORS", None)
    period = getattr(gen, "LESSON_SCHEDULE_PERIOD", None)
    if not isinstance(competitors, dict) or not competitors:
        raise RuntimeError("generator must declare non-empty LESSON_COMPETITORS")
    if not isinstance(period, int) or period < 2:
        raise RuntimeError("generator must declare LESSON_SCHEDULE_PERIOD >= 2")

    bands = [part.strip() for part in args.bands.split(",") if part.strip()]
    records = []
    ambiguity_count = 0
    weak_refutation_count = 0
    for band in bands:
        for start in range(period):
            pairs = [
                pair(gen, gen.generate(args.seed, start + offset, difficulty=band))
                for offset in range(period)
            ]
            disagreements = {
                name: sum(fn(item["input"]) != item["output"] for item in pairs)
                for name, fn in competitors.items()
            }
            weak = sorted(name for name, count in disagreements.items() if count < 2)
            weak_refutation_count += len(weak)
            rotations = []
            for query_index, query in enumerate(pairs):
                demos = [item for index, item in enumerate(pairs) if index != query_index]
                ambiguous = []
                for name, fn in competitors.items():
                    survives = all(fn(item["input"]) == item["output"] for item in demos)
                    if survives and fn(query["input"]) != query["output"]:
                        ambiguous.append(name)
                ambiguity_count += len(ambiguous)
                rotations.append({"query_index": query_index, "ambiguous": ambiguous})
            records.append(
                {
                    "band": band,
                    "start": start,
                    "profiles": [
                        gen.schedule_profile(args.seed, start + offset, band)
                        if hasattr(gen, "schedule_profile")
                        else None
                        for offset in range(period)
                    ],
                    "disagreements": disagreements,
                    "fewer_than_two_refutations": weak,
                    "rotations": rotations,
                }
            )

    result = {
        "schema": "arcpuzzles-selection-holdout-preflight-v1",
        "task_id": args.task_id,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "seed": args.seed,
        "bands": bands,
        "period": period,
        "label_source": "python_rule_mirror_not_racket_authority",
        "competitors": sorted(competitors),
        "cycles": len(records),
        "rotations": len(records) * period,
        "ambiguous_rival_predictions": ambiguity_count,
        "weak_refutation_entries": weak_refutation_count,
        "passed": ambiguity_count == 0
        and (not args.require_two_refutations or weak_refutation_count == 0),
        "records": records,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in result if k != "records"}, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
