#!/usr/bin/env python3
"""Measure profile coverage and shortcut refutation for 2fd7d58a066c.

This is a fast, task-local diagnostic.  It uses the generator's Python audit
mirror for comparisons; the repository battery remains the authority check
because it executes the canonical Racket rule.
"""
from __future__ import annotations

import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


TASK_ID = "2fd7d58a066c"
TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[1]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))


def _load_generator():
    path = TASK_ROOT / "generator.py"
    spec = importlib.util.spec_from_file_location(f"probe_generator_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_pairs() -> list[dict[str, Any]]:
    path = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        test = row["test"]
        return list(row["train"]) + ([test] if isinstance(test, dict) else list(test))
    raise RuntimeError(f"canonical row {TASK_ID} not found")


def _profile_signature(grid: list[list[int]]) -> tuple[int, int, int]:
    return (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )


def analyze(*, seed: int = 20261002, draws_per_band: int = 20) -> dict[str, Any]:
    """Return a JSON-serializable coverage and rival-refutation report."""
    if draws_per_band < 1:
        raise ValueError("draws_per_band must be positive")
    gen = _load_generator()

    profile_counts: Counter[str] = Counter()
    witness_hits: Counter[str] = Counter()
    shortcut_refutations: Counter[str] = Counter()
    first_refutations: dict[str, dict[str, Any]] = {}
    self_check_failures: list[dict[str, Any]] = []
    exact_canonical_profile_hits = 0
    total_draws = 0
    canonical_profiles = {(9, 9, 2), (10, 8, 2), (10, 10, 2)}

    for band_index, band in enumerate(("easy", "medium", "hard")):
        for sample_index in range(draws_per_band):
            draw_seed = seed + 100_003 * band_index
            grid = gen.generate(draw_seed, sample_index, difficulty=band)
            total_draws += 1
            errors = gen.self_check(grid, difficulty=band)
            if errors:
                self_check_failures.append(
                    {
                        "band": band,
                        "sample_index": sample_index,
                        "errors": list(errors),
                    }
                )

            observed = gen.observe_overrides(grid)
            profile = observed.get("scene_profile", "<unobserved>")
            profile_counts[profile] += 1
            exact_canonical_profile_hits += _profile_signature(grid) in canonical_profiles

            intended = gen.expected_output(grid)
            for name, predicate in gen.SEMANTIC_WITNESSES.items():
                witness_hits[name] += bool(predicate(grid))
            for name, rival in gen.CANONICAL_SHORTCUTS.items():
                rival_output = rival(grid)
                if rival_output == intended:
                    continue
                shortcut_refutations[name] += 1
                first_refutations.setdefault(
                    name,
                    {
                        "band": band,
                        "sample_index": sample_index,
                        "scene_profile": profile,
                        "input": grid,
                        "intended_output": intended,
                        "rival_output": rival_output,
                    },
                )

    lesson_pairs = []
    for sample_index in range(gen.EXAMPLES_NEEDED + 1):
        grid = gen.generate(seed, sample_index, difficulty="medium")
        lesson_pairs.append({"input": grid, "output": gen.expected_output(grid)})
    lesson_reasons = gen.lesson_identifiable(
        lesson_pairs[: gen.EXAMPLES_NEEDED], lesson_pairs[gen.EXAMPLES_NEEDED]
    )

    canonical_pairs = _canonical_pairs()
    canonical_mirror_mismatches = []
    canonical_shortcut_fit = {name: True for name in gen.CANONICAL_SHORTCUTS}
    for pair_index, pair in enumerate(canonical_pairs):
        if gen.expected_output(pair["input"]) != pair["output"]:
            canonical_mirror_mismatches.append(pair_index)
        for name, rival in gen.CANONICAL_SHORTCUTS.items():
            if rival(pair["input"]) != pair["output"]:
                canonical_shortcut_fit[name] = False

    return {
        "schema": "2fd7d58a066c-profile-probe-v1",
        "seed": seed,
        "draws_per_band": draws_per_band,
        "total_draws": total_draws,
        "profile_counts": dict(sorted(profile_counts.items())),
        "exact_canonical_profile_hits": exact_canonical_profile_hits,
        "exact_canonical_profile_rate": exact_canonical_profile_hits / total_draws,
        "witness_hits": dict(sorted(witness_hits.items())),
        "canonical_shortcut_refutations": dict(sorted(shortcut_refutations.items())),
        "first_refutations": first_refutations,
        "self_check_failures": self_check_failures,
        "lesson_identifiable": lesson_reasons,
        "canonical_pair_count": len(canonical_pairs),
        "canonical_mirror_mismatches": canonical_mirror_mismatches,
        "canonical_shortcut_fit": canonical_shortcut_fit,
        "authority_note": (
            "Python audit mirror only; use the repository battery semantic/rule "
            "stages for Racket-authoritative verification."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261002)
    parser.add_argument("--draws-per-band", type=int, default=20)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    report = analyze(seed=args.seed, draws_per_band=args.draws_per_band)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        sys.stdout.write(text)
    return 0 if not report["self_check_failures"] and not report["lesson_identifiable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
