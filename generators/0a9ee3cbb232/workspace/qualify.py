#!/usr/bin/env python3
"""Fast source-bound qualification probe for generator 0a9ee3cbb232.

This complements the shared battery with task-specific checks that are cheap to
rerun while editing: exact override Cartesian support, default witness coverage,
and every cyclic query rotation of short lessons against the declared rivals.
It uses an independent pixel oracle from ``reference_probe.py`` and never treats
that oracle as canonical label authority.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import itertools
import json
from pathlib import Path
from typing import Any

from reference_probe import (
    canonical_pairs,
    connected_components_output,
    drop_twos_on_overflow_output,
    lesson,
    load_generator,
    observed,
    occupied_rows_output,
    rule_output,
)

BANDS = ("easy", "medium", "hard")
BACKGROUNDS = (0, 1, 4, 5, 6, 7, 8, 9)
RIVALS = {
    "connected_components": connected_components_output,
    "occupied_rows": occupied_rows_output,
    "drop_twos_on_overflow": drop_twos_on_overflow_output,
}


def _grid_key(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def audit(
    *,
    samples_per_band: int = 100,
    cyclic_starts: int = 16,
    full_cartesian: bool = True,
) -> dict[str, Any]:
    """Return a JSON-serializable qualification report; never hide failures."""
    if samples_per_band < 1 or cyclic_starts < 1:
        raise ValueError("samples_per_band and cyclic_starts must be positive")

    gen = load_generator()
    generator_path = Path(gen.__file__).resolve()
    errors: list[str] = []

    pairs = canonical_pairs()
    for index, pair in enumerate(pairs):
        issues = gen.self_check(pair["input"])
        if issues:
            errors.append(f"canonical[{index}] rejected: {issues}")
        if rule_output(pair["input"]) != pair["output"]:
            errors.append(f"canonical[{index}] independent oracle mismatch")
        if gen._mirror(pair["input"]) != pair["output"]:
            errors.append(f"canonical[{index}] generator mirror mismatch")

    canonical_rival_fit = {
        name: sum(rival(pair["input"]) == pair["output"] for pair in pairs)
        for name, rival in RIVALS.items()
    }
    for name, fits in canonical_rival_fit.items():
        if fits != len(pairs):
            errors.append(f"declared canonical shortcut {name} fits {fits}/{len(pairs)}")

    exact_cases = 0
    if full_cartesian:
        for case_index, values in enumerate(
            itertools.product(range(5), range(1, 7), range(1, 7), BACKGROUNDS)
        ):
            profile, n3, n2, background = values
            expected = {
                "canvas_profile": profile,
                "n_3": n3,
                "n_2": n2,
                "background": background,
            }
            band = BANDS[case_index % len(BANDS)]
            grid = gen.generate(1701 + case_index, case_index, difficulty=band, **expected)
            exact_cases += 1
            if gen.self_check(grid):
                errors.append(f"exact case {case_index} rejected")
                continue
            if observed(grid) != expected or gen.observe_overrides(grid) != expected:
                errors.append(f"exact case {case_index} not observable: {observed(grid)} != {expected}")
            if rule_output(grid) != gen._mirror(grid):
                errors.append(f"exact case {case_index} mirror mismatch")

    input_keys: set[tuple[tuple[int, ...], ...]] = set()
    output_keys: set[tuple[tuple[int, ...], ...]] = set()
    profiles: set[int] = set()
    backgrounds: set[int] = set()
    witness_counts = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    default_draws = 0
    for band_index, band in enumerate(BANDS):
        for index in range(samples_per_band):
            seed = 3100 + band_index * 100_000 + index
            grid = gen.generate(seed, index, difficulty=band)
            default_draws += 1
            issues = gen.self_check(grid)
            if issues:
                errors.append(f"default {band}/{index} rejected: {issues}")
                continue
            expected = rule_output(grid)
            if gen._mirror(grid) != expected:
                errors.append(f"default {band}/{index} mirror mismatch")
            input_keys.add(_grid_key(grid))
            output_keys.add(_grid_key(expected))
            values = observed(grid)
            profiles.add(values["canvas_profile"])
            backgrounds.add(values["background"])
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                fires = bool(witness(grid))
                witness_counts[name] += int(fires)
                if fires:
                    for rival_name in gen.WITNESS_RIVALS.get(name, ()):
                        if gen.SEMANTIC_RIVALS[rival_name](grid) == expected:
                            errors.append(
                                f"default {band}/{index}: witness {name} did not refute {rival_name}"
                            )

    cyclic_windows = 0
    for band in BANDS:
        for start in range(cyclic_starts):
            pairs4 = lesson(8800 + start, start, band)
            for query_index, query in enumerate(pairs4):
                demos = [pair for i, pair in enumerate(pairs4) if i != query_index]
                cyclic_windows += 1
                reasons = gen.lesson_identifiable(deepcopy(demos), deepcopy(query))
                if reasons:
                    errors.append(
                        f"lesson {band}/{start}/q{query_index} hook warnings: {reasons}"
                    )
                for name, rival in gen.LESSON_COMPETITORS.items():
                    if all(rival(demo["input"]) == demo["output"] for demo in demos):
                        errors.append(
                            f"lesson {band}/{start}/q{query_index}: rival {name} survives demos"
                        )

    report = {
        "schema": "0a9ee3cbb232-qualification-v1",
        "status": "pass" if not errors else "fail",
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "canonical_pairs": len(pairs),
        "canonical_rival_fit": canonical_rival_fit,
        "exact_overrides": {
            "enabled": full_cartesian,
            "cases": exact_cases,
        },
        "defaults": {
            "draws": default_draws,
            "unique_inputs": len(input_keys),
            "distinct_outputs": len(output_keys),
            "canvas_profiles": sorted(profiles),
            "backgrounds": sorted(backgrounds),
            "witness_counts": witness_counts,
        },
        "lessons": {
            "starts_per_band": cyclic_starts,
            "cyclic_windows": cyclic_windows,
            "competitors": sorted(gen.LESSON_COMPETITORS),
        },
        "errors": errors[:200],
        "error_count": len(errors),
        "limits": [
            "Finite declared-rival checks are not a proof of universal identifiability.",
            "The independent Python oracle is review tooling, not label authority.",
            "Use the shared Racket battery for authority and execution parity.",
        ],
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples-per-band", type=int, default=100)
    parser.add_argument("--cyclic-starts", type=int, default=16)
    parser.add_argument("--skip-cartesian", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = audit(
        samples_per_band=args.samples_per_band,
        cyclic_starts=args.cyclic_starts,
        full_cartesian=not args.skip_cartesian,
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
