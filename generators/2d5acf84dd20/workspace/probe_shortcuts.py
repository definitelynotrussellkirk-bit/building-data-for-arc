#!/usr/bin/env python3
"""Replayable shortcut and lesson-window probe for task 2d5acf84dd20.

Run from anywhere in an extracted review packet. The probe discovers the repo,
loads the selected generator without sibling imports, verifies every declared
canonical shortcut against every canonical pair, searches production draws for
an emitted counterexample, and checks all cyclic starts of the four-profile
lesson schedule.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


TASK_ID = "2d5acf84dd20"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_generator(repo: Path):
    runtime = repo / "shared" / "runtime"
    src = repo / "src"
    for path in (runtime, src):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    path = repo / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(
        f"shortcut_probe_{TASK_ID}", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _grid_sha256(grid: Any) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()


def _canonical_pairs(repo: Path) -> list[dict[str, Any]]:
    from reviewer_support import canonical_pairs

    return canonical_pairs(TASK_ID, root=repo)


def _probe(args: argparse.Namespace) -> dict[str, Any]:
    repo = _repo_root()
    gen, generator_path = _load_generator(repo)
    canonical = _canonical_pairs(repo)
    bands = ("easy", "medium", "hard")

    shortcut_results: dict[str, Any] = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        canonical_mismatches = [
            index
            for index, pair in enumerate(canonical)
            if rival(pair["input"]) != pair["output"]
        ]
        witness = None
        for band in bands:
            for sample_index in range(args.samples_per_band):
                grid = gen.generate(args.seed, sample_index, difficulty=band)
                oracle = gen.rule_mirror(grid)
                rival_output = rival(grid)
                if rival_output == oracle:
                    continue
                witness = {
                    "seed": args.seed,
                    "sample_index": sample_index,
                    "difficulty": band,
                    "input_sha256": _grid_sha256(grid),
                    "observed_overrides": gen.observe_overrides(grid),
                    "input": grid,
                    "oracle_output": oracle,
                    "rival_output": rival_output,
                }
                break
            if witness is not None:
                break
        shortcut_results[name] = {
            "fits_all_canonical_pairs": not canonical_mismatches,
            "canonical_mismatch_indices": canonical_mismatches,
            "generated_counterexample": witness,
        }

    period = len(gen.SCHEDULE_PROFILES)
    window_results = []
    for band in bands:
        for start in range(period):
            demos = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(args.seed, sample_index, difficulty=band)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(
                args.seed,
                start + gen.EXAMPLES_NEEDED,
                difficulty=band,
            )
            reasons = gen.lesson_identifiable(demos, {"input": query_grid})
            survivors = [
                name
                for name, rival in gen.LESSON_COMPETITORS.items()
                if all(rival(pair["input"]) == pair["output"] for pair in demos)
            ]
            window_results.append(
                {
                    "difficulty": band,
                    "start": start,
                    "identifiability_reasons": reasons,
                    "surviving_competitors": survivors,
                }
            )

    failures = []
    for name, result in shortcut_results.items():
        if not result["fits_all_canonical_pairs"]:
            failures.append(f"{name} does not fit every canonical pair")
        if result["generated_counterexample"] is None:
            failures.append(f"no generated counterexample found for {name}")
    for window in window_results:
        if window["identifiability_reasons"] or window["surviving_competitors"]:
            failures.append(
                f"lesson window {window['difficulty']}:{window['start']} is ambiguous"
            )

    return {
        "schema": "arcpuzzles-task-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": _sha256(generator_path),
        "rule_hash": gen.RULE_HASH,
        "seed": args.seed,
        "samples_per_band": args.samples_per_band,
        "canonical_pair_count": len(canonical),
        "shortcuts": shortcut_results,
        "cyclic_window_results": window_results,
        "failures": failures,
        "status": "pass" if not failures else "fail",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=1993158372)
    parser.add_argument("--samples-per-band", type=int, default=64)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = _probe(args)
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    summary = {
        "task_id": report["task_id"],
        "generator_sha256": report["generator_sha256"],
        "status": report["status"],
        "shortcuts": {
            name: {
                "fits_canonical": result["fits_all_canonical_pairs"],
                "counterexample": result["generated_counterexample"] is not None,
            }
            for name, result in report["shortcuts"].items()
        },
        "windows_checked": len(report["cyclic_window_results"]),
        "failures": report["failures"],
        "out": str(args.out) if args.out else None,
    }
    print(json.dumps(summary, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
