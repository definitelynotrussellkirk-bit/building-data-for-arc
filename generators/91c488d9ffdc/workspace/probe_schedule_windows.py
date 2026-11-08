#!/usr/bin/env python3
"""Enumerate consecutive teaching windows and report surviving semantic rivals.

This is a task-local authoring probe, not part of generation. It closes a gap in
random lesson sampling: a periodic curriculum can look healthy overall while one
cyclic start still leaves a shortcut consistent with every demonstration.

From the repository root, one portable invocation is::

    PYTHONPATH=shared/runtime python \
      generators/91c488d9ffdc/workspace/probe_schedule_windows.py \
      --starts 18 --require-identifiable \
      --out ../checks/schedule-window-probe.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable

TASK_ID = "91c488d9ffdc"
GENERATOR_MODULE = f"puzzle_generators.per_puzzle.{TASK_ID}.generator"


def _load_generator():
    """Import the staged generator, falling back to the sibling source file."""
    try:
        return importlib.import_module(GENERATOR_MODULE)
    except ModuleNotFoundError as exc:
        # Only fall back when the task module itself is absent. Missing runtime
        # dependencies should remain visible rather than being masked.
        if exc.name not in {
            GENERATOR_MODULE,
            f"puzzle_generators.per_puzzle.{TASK_ID}",
        }:
            raise
        source = Path(__file__).resolve().parents[1] / "generator.py"
        spec = importlib.util.spec_from_file_location(
            f"schedule_probe_{TASK_ID}", source
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"could not load generator source: {source}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


def _source_sha256(module: Any) -> str:
    path = Path(module.__file__).resolve()
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pair(generator: Any, seed: int, sample_index: int, band: str) -> dict[str, Any]:
    grid = generator.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": generator.rule_mirror(grid)}


def _surviving_rivals(generator: Any, demos: list[dict[str, Any]]) -> list[str]:
    survivors = []
    for name, rival in generator.LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            survivors.append(name)
    return sorted(survivors)


def probe_schedule(
    *,
    seed: int = 555,
    starts: int = 18,
    bands: Iterable[str] = ("easy", "medium", "hard"),
) -> dict[str, Any]:
    """Return a deterministic report for every requested consecutive window."""
    if isinstance(starts, bool) or not isinstance(starts, int) or starts < 1:
        raise ValueError("starts must be a positive integer")

    generator = _load_generator()
    examples_needed = int(generator.EXAMPLES_NEEDED)
    if examples_needed < 1:
        raise ValueError("EXAMPLES_NEEDED must be positive")

    windows: list[dict[str, Any]] = []
    profiles_seen: set[str] = set()
    for band in bands:
        for start in range(starts):
            demos = [
                _pair(generator, seed, index, band)
                for index in range(start, start + examples_needed)
            ]
            query = _pair(generator, seed, start + examples_needed, band)
            profiles = [
                generator.schedule_profile(seed, index, difficulty=band)
                for index in range(start, start + examples_needed)
            ]
            profiles_seen.update(profiles)
            surviving = _surviving_rivals(generator, demos)
            query_changing_survivors = [
                name
                for name in surviving
                if generator.LESSON_COMPETITORS[name](query["input"])
                != query["output"]
            ]
            reasons = generator.lesson_identifiable(demos, query)
            windows.append(
                {
                    "band": band,
                    "start": start,
                    "demo_indices": list(range(start, start + examples_needed)),
                    "query_index": start + examples_needed,
                    "profiles": profiles,
                    "surviving_rivals": surviving,
                    "query_changing_survivors": query_changing_survivors,
                    "identifiable": not reasons,
                    "reasons": reasons,
                }
            )

    failures = [window for window in windows if not window["identifiable"]]
    return {
        "schema": "arcpuzzles-task-schedule-window-probe-v1",
        "task_id": TASK_ID,
        "generator_version": generator.VERSION,
        "generator_sha256": _source_sha256(generator),
        "rule_hash": generator.RULE_HASH,
        "policy": {
            "seed": seed,
            "starts_per_band": starts,
            "bands": list(bands),
            "examples_needed": examples_needed,
            "query_policy": "next consecutive sample after the demonstrations",
        },
        "summary": {
            "windows_checked": len(windows),
            "identifiable_windows": len(windows) - len(failures),
            "unidentifiable_windows": len(failures),
            "profiles_seen": sorted(profiles_seen),
        },
        "windows": windows,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=555)
    parser.add_argument("--starts", type=int, default=18)
    parser.add_argument(
        "--bands",
        nargs="+",
        default=["easy", "medium", "hard"],
        choices=["easy", "medium", "hard"],
    )
    parser.add_argument("--out", type=Path)
    parser.add_argument(
        "--require-identifiable",
        action="store_true",
        help="exit nonzero if any consecutive window leaves a query-changing rival",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = probe_schedule(seed=args.seed, starts=args.starts, bands=args.bands)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(text, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
        print(args.out)
    if args.require_identifiable and report["summary"]["unidentifiable_windows"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
