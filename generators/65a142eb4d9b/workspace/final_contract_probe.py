#!/usr/bin/env python3
"""Replayable high-coverage contract probe for task 65a142eb4d9b.

This reviewer helper exercises every advertised joint override combination and
all cyclic curriculum windows.  It intentionally uses the independent oracle
from ``reference_probe`` rather than treating the generator mirror as authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from itertools import product
from pathlib import Path

from reference_probe import analysis, canonical_pairs, load_generator, rule_output

BANDS = (None, "easy", "medium", "hard")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    home = Path(__file__).resolve().parents[1]
    generator_path = home / "generator.py"
    gen = load_generator(generator_path)

    override_failures = []
    override_cases = 0
    for band, h, w, n_expandable, n_dominoes in product(
        BANDS, range(7, 11), range(7, 11), range(1, 6), range(2)
    ):
        case = {
            "grid_h": h,
            "grid_w": w,
            "n_expandable_cells": n_expandable,
            "n_blocked_dominoes": n_dominoes,
        }
        seed = 100_000 + override_cases
        sample_index = override_cases % len(gen.SCHEDULE_PROFILES)
        override_cases += 1
        try:
            grid = gen.generate(seed, sample_index, difficulty=band, **case)
            observed = gen.observe_overrides(grid)
            failures = gen.self_check(grid)
            if observed != case:
                override_failures.append({"case": case, "band": band, "observed": observed})
            elif failures:
                override_failures.append({"case": case, "band": band, "errors": failures})
            elif gen.rule_mirror(grid) != rule_output(grid):
                override_failures.append({"case": case, "band": band, "error": "oracle mismatch"})
            elif grid != gen.generate(seed, sample_index, difficulty=band, **case):
                override_failures.append({"case": case, "band": band, "error": "nondeterministic"})
        except Exception as exc:  # probe must retain all failures
            override_failures.append(
                {"case": case, "band": band, "exception": f"{type(exc).__name__}: {exc}"}
            )

    lesson_failures = []
    lesson_windows = 0
    for band, seed_offset, start in product(("easy", "medium", "hard"), range(10), range(6)):
        pairs = []
        for offset in range(4):
            seed = 200_000 + 1000 * seed_offset + start
            grid = gen.generate(seed, start + offset, difficulty=band)
            pairs.append({"input": grid, "output": rule_output(grid)})
        lesson_windows += 1
        reasons = gen.lesson_identifiable(pairs[:3], pairs[3])
        if reasons:
            lesson_failures.append(
                {"band": band, "seed_offset": seed_offset, "start": start, "reasons": reasons}
            )

    canonical = canonical_pairs()
    shortcut_fit = {
        name: sum(rival(pair["input"]) == pair["output"] for pair in canonical)
        for name, rival in gen.CANONICAL_SHORTCUTS.items()
    }

    profile_witnesses = {}
    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(300_000, index, difficulty=band) for index in range(6)]
        profile_witnesses[band] = {
            witness: [
                gen.schedule_profile(300_000, index, difficulty=band)
                for index, grid in enumerate(grids)
                if predicate(grid)
            ]
            for witness, predicate in gen.SEMANTIC_WITNESSES.items()
        }

    report = {
        "schema": "65a142eb4d9b-final-contract-probe-v1",
        "generator_sha256": sha256(generator_path),
        "override_cases": override_cases,
        "override_failures": override_failures,
        "cyclic_lesson_windows": lesson_windows,
        "lesson_failures": lesson_failures,
        "canonical_pairs": len(canonical),
        "canonical_shortcut_fit_counts": shortcut_fit,
        "profile_witnesses": profile_witnesses,
        "status": "PASS" if not override_failures and not lesson_failures else "FAIL",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "override_cases": override_cases,
        "cyclic_lesson_windows": lesson_windows,
        "out": str(args.out),
    }))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
