#!/usr/bin/env python3
"""Reproducible distribution/shortcut probe for generator 4cfd24806fb2."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[1]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

_SPEC = importlib.util.spec_from_file_location(
    "generator_4cfd24806fb2_probe", TASK_ROOT / "generator.py"
)
assert _SPEC is not None and _SPEC.loader is not None
GEN = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(GEN)


def analyze(seed: int = 20261002, draws_per_band: int = 8) -> dict[str, Any]:
    profile_counts: Counter[str] = Counter()
    witness_counts: Counter[str] = Counter()
    shortcut_refutations: Counter[str] = Counter()
    strict_hits: Counter[str] = Counter()
    self_check_failures: list[dict[str, Any]] = []

    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(draws_per_band):
            sample_index = band_index * draws_per_band + index
            grid = GEN.generate(seed, sample_index, difficulty=band)
            errors = GEN.self_check(grid)
            if errors:
                self_check_failures.append(
                    {"band": band, "sample_index": sample_index, "errors": errors}
                )
                continue
            profile = GEN.observe_overrides(grid).get("scene_profile", "unclassified")
            profile_counts[profile] += 1
            strict_hits[band] += GEN.strict_canonical_like(grid) == []
            authoritative = GEN.expected_output(grid)
            for name, predicate in GEN.SEMANTIC_WITNESSES.items():
                witness_counts[name] += bool(predicate(grid))
            for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
                shortcut_refutations[name] += shortcut(grid) != authoritative

    lesson = []
    for index in range(GEN.EXAMPLES_NEEDED + 1):
        grid = GEN.generate(seed + 1, index, difficulty="medium")
        lesson.append({"input": grid, "output": GEN.expected_output(grid)})

    return {
        "task_id": GEN.TASK_ID,
        "version": GEN.VERSION,
        "seed": seed,
        "draws_per_band": draws_per_band,
        "total_draws": draws_per_band * 3,
        "profile_counts": dict(sorted(profile_counts.items())),
        "strict_rate_by_band": {
            band: strict_hits[band] / draws_per_band
            for band in ("easy", "medium", "hard")
        },
        "witness_counts": dict(sorted(witness_counts.items())),
        "canonical_shortcut_refutations": dict(sorted(shortcut_refutations.items())),
        "self_check_failures": self_check_failures,
        "lesson_identifiable": GEN.lesson_identifiable(
            lesson[: GEN.EXAMPLES_NEEDED], lesson[GEN.EXAMPLES_NEEDED]
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261002)
    parser.add_argument("--draws-per-band", type=int, default=8)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = analyze(args.seed, args.draws_per_band)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    print(rendered, end="")
    return 0 if not report["self_check_failures"] and not report["lesson_identifiable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
