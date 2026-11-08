#!/usr/bin/env python3
"""Fast, task-local semantic audit for ``ec9340d27f7e``.

This is intentionally independent of the heavyweight Racket battery.  It gives
future reviewers a reproducible first look at profile coverage, strict-anchor
rate, witness firing, named-rival disagreement, and consecutive lesson
identifiability.  The official semantic gate remains the authority because it
checks rivals against the canonical Racket rule; this probe is a fast diagnostic
that runs directly from the task directory.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

TASK_ID = "ec9340d27f7e"
HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load_generator():
    path = HERE.parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location(f"semantic_probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load generator at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pair(module, grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": module.rule_mirror(grid)}


def build_report(samples_per_band: int = 32) -> dict[str, Any]:
    if samples_per_band < 1:
        raise ValueError("samples_per_band must be positive")
    module = _load_generator()
    bands = ("easy", "medium", "hard")
    profile_counts: Counter[str] = Counter()
    witness_counts: Counter[str] = Counter()
    rival_disagreements: Counter[str] = Counter()
    strict = 0
    contrast = 0
    draws = 0
    examples: dict[str, dict[str, Any]] = {}

    for band_index, band in enumerate(bands):
        for sample_index in range(samples_per_band):
            seed = 1_000_003 + 100_003 * band_index + 7919 * sample_index
            grid = module.generate(seed, sample_index, difficulty=band)
            draws += 1
            profile = module.schedule_profile(seed, sample_index, difficulty=band)
            profile_counts[profile] += 1
            intended = module.rule_mirror(grid)
            if module.strict_canonical_like(grid) == []:
                strict += 1
            else:
                contrast += 1
            for name, predicate in module.SEMANTIC_WITNESSES.items():
                if predicate(grid):
                    witness_counts[name] += 1
                    examples.setdefault(
                        name,
                        {
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "profile": profile,
                            "grid": grid,
                        },
                    )
            for name, rival in module.SEMANTIC_RIVALS.items():
                if rival(grid) != intended:
                    rival_disagreements[name] += 1

    lesson_failures: list[dict[str, Any]] = []
    # Probe more starts than one schedule period when affordable.  Consecutive
    # indices match the official lesson materialization contract.
    lesson_starts = max(8, min(32, samples_per_band * 2))
    for band_index, band in enumerate(bands):
        for start in range(lesson_starts):
            seed = 9_000_001 + 1_000_003 * band_index + start
            pairs = [
                _pair(module, module.generate(seed, start + offset, difficulty=band))
                for offset in range(module.EXAMPLES_NEEDED + 1)
            ]
            reasons = module.lesson_identifiable(
                pairs[: module.EXAMPLES_NEEDED], pairs[module.EXAMPLES_NEEDED]
            )
            if reasons:
                lesson_failures.append(
                    {"band": band, "start": start, "seed": seed, "reasons": reasons}
                )

    return {
        "schema": "ec9340d27f7e-semantic-probe/1",
        "task_id": TASK_ID,
        "generator_version": module.VERSION,
        "rule_hash": module.RULE_HASH,
        "samples_per_band": samples_per_band,
        "draws": draws,
        "profile_counts": dict(sorted(profile_counts.items())),
        "strict": {"count": strict, "rate": strict / draws},
        "contrast": {"count": contrast, "rate": contrast / draws},
        "witness_counts": {
            name: witness_counts[name] for name in module.SEMANTIC_WITNESSES
        },
        "rival_disagreements": {
            name: rival_disagreements[name] for name in module.SEMANTIC_RIVALS
        },
        "lesson_windows_checked": len(bands) * lesson_starts,
        "lesson_failures": lesson_failures,
        "first_witness_examples": examples,
    }


def _summary(report: dict[str, Any]) -> str:
    return (
        f"{report['task_id']} v{report['generator_version']}: "
        f"{report['draws']} draws, strict {report['strict']['count']}/"
        f"{report['draws']} ({report['strict']['rate']:.1%}), "
        f"profiles {len(report['profile_counts'])}, "
        f"witnesses firing {sum(v > 0 for v in report['witness_counts'].values())}/"
        f"{len(report['witness_counts'])}, rivals refuted "
        f"{sum(v > 0 for v in report['rival_disagreements'].values())}/"
        f"{len(report['rival_disagreements'])}, lesson failures "
        f"{len(report['lesson_failures'])}/{report['lesson_windows_checked']}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples-per-band", type=int, default=32)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)
    try:
        report = build_report(args.samples_per_band)
    except (OSError, RuntimeError, ValueError, AssertionError) as exc:
        print(f"semantic-probe: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(_summary(report))
    return 1 if report["lesson_failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
