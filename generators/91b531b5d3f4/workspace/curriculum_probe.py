#!/usr/bin/env python3
"""Reproduce the four-example curriculum and shortcut-separation claims.

Run from the repository root (or any directory):

    python3 generators/91b531b5d3f4/workspace/curriculum_probe.py --windows 12

The probe uses only the task generator's declared semantic hooks.  It is a fast
review aid, not a replacement for the repository battery or Racket execution.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

TASK_ID = "91b531b5d3f4"
HERE = Path(__file__).resolve().parent
GENERATOR_PATH = HERE.parent / "generator.py"
REPO_ROOT = HERE.parents[2]
RUNTIME = REPO_ROOT / "shared" / "runtime"


def _load_generator():
    runtime = str(RUNTIME)
    if runtime not in sys.path:
        sys.path.insert(0, runtime)
    name = f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _pair(gen, grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": gen._rule_mirror(grid)}


def build_report(*, seed: int = 303, windows: int = 12) -> dict[str, Any]:
    """Return a JSON-safe report over consecutive complete lesson windows."""
    if windows < 1:
        raise ValueError("windows must be at least 1")

    gen = _load_generator()
    examples_needed = int(gen.EXAMPLES_NEEDED)
    declared_profiles = tuple(gen.SCHEDULE_PROFILES)
    declared_rivals = tuple(gen.LESSON_COMPETITORS)
    bands: dict[str, Any] = {}

    for band_index, band in enumerate(("easy", "medium", "hard")):
        failures: list[dict[str, Any]] = []
        rivals_refuted: set[str] = set()
        texture_counts = {profile: 0 for profile in declared_profiles}
        mixed_feature_counts = {
            "empty_column_markers": 0,
            "live_column_distractors": 0,
            "empty_column_distractors": 0,
            "misaligned_header_color_distractors": 0,
        }

        for window in range(windows):
            start = window * examples_needed
            window_seed = seed + band_index * 10_000 + window
            grids = [
                gen.generate(window_seed, start + offset, difficulty=band)
                for offset in range(examples_needed)
            ]
            analyses = [gen._analysis(grid) for grid in grids]
            textures = [analysis["texture"] for analysis in analyses]
            for texture in textures:
                if texture in texture_counts:
                    texture_counts[texture] += 1

            expected = set(declared_profiles)
            if set(textures) != expected or len(textures) != len(expected):
                failures.append(
                    {
                        "window": window,
                        "kind": "profile_coverage",
                        "observed": textures,
                        "expected": list(declared_profiles),
                    }
                )

            invalid = [
                {"offset": offset, "errors": analysis["errors"]}
                for offset, analysis in enumerate(analyses)
                if analysis["errors"]
            ]
            if invalid:
                failures.append(
                    {"window": window, "kind": "invalid_generated_grid", "details": invalid}
                )

            strict_count = sum(gen.strict_canonical_like(grid) for grid in grids)
            if strict_count != 1:
                failures.append(
                    {
                        "window": window,
                        "kind": "strict_anchor_count",
                        "observed": strict_count,
                        "expected": 1,
                    }
                )

            demos = [_pair(gen, grid) for grid in grids]
            query_grid = gen.generate(
                window_seed,
                start + examples_needed,
                difficulty=band,
            )
            identifiability_errors = gen.lesson_identifiable(
                demos, _pair(gen, query_grid)
            )
            if identifiability_errors:
                failures.append(
                    {
                        "window": window,
                        "kind": "lesson_not_identifiable",
                        "errors": identifiability_errors,
                    }
                )

            for name, rival in gen.LESSON_COMPETITORS.items():
                if any(rival(pair["input"]) != pair["output"] for pair in demos):
                    rivals_refuted.add(name)
                else:
                    failures.append(
                        {
                            "window": window,
                            "kind": "unrefuted_rival",
                            "rival": name,
                        }
                    )

            mixed = next(
                analysis
                for analysis in analyses
                if analysis["texture"] == "mixed_witnesses"
            )
            for key in mixed_feature_counts:
                mixed_feature_counts[key] += int(mixed[key])

        missing_rivals = sorted(set(declared_rivals) - rivals_refuted)
        if missing_rivals:
            failures.append(
                {"kind": "rivals_never_refuted", "rivals": missing_rivals}
            )

        bands[band] = {
            "windows_checked": windows,
            "lessons_checked": windows,
            "texture_counts": texture_counts,
            "mixed_feature_counts": mixed_feature_counts,
            "rivals_refuted": sorted(rivals_refuted),
            "failures": failures,
        }

    return {
        "schema": "arc-curriculum-probe-v1",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "seed": seed,
        "windows_per_band": windows,
        "examples_needed": examples_needed,
        "declared_profiles": list(declared_profiles),
        "declared_rivals": list(declared_rivals),
        "bands": bands,
        "ok": all(not summary["failures"] for summary in bands.values()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=303)
    parser.add_argument("--windows", type=int, default=12)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    report = build_report(seed=args.seed, windows=args.windows)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        sys.stdout.write(payload)
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
