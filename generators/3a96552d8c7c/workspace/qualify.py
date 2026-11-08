#!/usr/bin/env python3
"""Source-only qualification probe for generator 3a96552d8c7c.

This is intentionally smaller than the repository battery.  It gives a future
agent a fast, reproducible local check of the failure modes specific to this
repair: canonical ownership, exact-axis observability, one-zero boundary
support, semantic witness/rival authority, and lesson query rotations.

It does not execute Racket.  Labels come from the independent Python mirror in
``reference_probe.py``; the repository battery remains the authority check.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from reference_probe import analyze, independent_rule, load_generator

BANDS = ("easy", "medium", "hard")
AXIS_KEYS = ("grid_h", "grid_w", "n_fill_rows", "span_style", "negative_mode")

_OVERRIDE_CASES = (
    dict(grid_h=6, grid_w=8, n_fill_rows=2, span_style="short", negative_mode="none"),
    dict(grid_h=7, grid_w=10, n_fill_rows=3, span_style="long", negative_mode="blocked"),
    dict(grid_h=8, grid_w=11, n_fill_rows=4, span_style="mixed", negative_mode="three_fives"),
    dict(grid_h=9, grid_w=12, n_fill_rows=2, span_style="short", negative_mode="wrong_color"),
    dict(grid_h=10, grid_w=14, n_fill_rows=4, span_style="mixed", negative_mode="mixed"),
)


def _digest_grid(grid: list[list[int]]) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _safe_reasons(gen, demos, query) -> tuple[list[str], str | None]:
    try:
        reasons = gen.lesson_identifiable(copy.deepcopy(demos), copy.deepcopy(query))
    except Exception as exc:  # diagnostic tool: preserve and continue
        return [], f"{type(exc).__name__}: {exc}"
    if not isinstance(reasons, (list, tuple)) or any(not isinstance(x, str) for x in reasons):
        return [], f"invalid return {reasons!r}"
    return list(reasons), None


def _canonical_check(gen) -> dict[str, Any]:
    result: dict[str, Any] = {"pairs": 0, "failures": 0, "errors": []}
    try:
        from reviewer_support import canonical_pairs, find_root

        pairs = canonical_pairs(gen.TASK_ID, root=find_root(__file__))
    except Exception as exc:
        result["errors"].append(f"canonical load: {type(exc).__name__}: {exc}")
        result["failures"] += 1
        return result
    result["pairs"] = len(pairs)
    for index, pair in enumerate(pairs):
        failures: list[str] = []
        try:
            findings = list(gen.self_check(copy.deepcopy(pair["input"])) or [])
            if findings:
                failures.append(f"self_check={findings[:3]}")
            expected = pair["output"]
            if independent_rule(pair["input"]) != expected:
                failures.append("independent mirror mismatch")
            if gen.rule_mirror(copy.deepcopy(pair["input"])) != expected:
                failures.append("generator mirror mismatch")
        except Exception as exc:
            failures.append(f"{type(exc).__name__}: {exc}")
        if failures:
            result["failures"] += 1
            result["errors"].append(f"pair {index}: " + "; ".join(failures))
    return result


def _population_check(gen, *, per_band: int, seed: int) -> dict[str, Any]:
    witness_counts: Counter[str] = Counter({name: 0 for name in gen.SEMANTIC_WITNESSES})
    rival_disagreements: Counter[str] = Counter({name: 0 for name in gen.SEMANTIC_RIVALS})
    profile_counts: Counter[str] = Counter()
    band_counts: dict[str, Counter[str]] = {band: Counter() for band in BANDS}
    unique: set[str] = set()
    errors: list[str] = []
    totals = Counter()

    for band_index, band in enumerate(BANDS):
        for index in range(per_band):
            draw_seed = int(seed) + 1009 * band_index + 7919 * index
            sample_index = index
            totals["draws"] += 1
            label = f"{band}[{index}] seed={draw_seed} sample_index={sample_index}"
            try:
                grid = gen.generate(draw_seed, sample_index, difficulty=band)
                unique.add(_digest_grid(grid))
                findings = list(gen.self_check(copy.deepcopy(grid)) or [])
                if findings:
                    totals["self_check_failures"] += 1
                    errors.append(f"{label}: self_check {findings[:3]}")
                strict = gen.strict_canonical_like(copy.deepcopy(grid))
                if strict not in (True, []) and strict is not None:
                    totals["strict_failures"] += 1
                expected = independent_rule(grid)
                if expected == grid:
                    totals["identity_outputs"] += 1
                    errors.append(f"{label}: authority mirror is identity")
                if gen.rule_mirror(copy.deepcopy(grid)) != expected:
                    totals["rule_mirror_mismatches"] += 1
                    errors.append(f"{label}: rule_mirror differs from independent mirror")
                declared = gen.observe_overrides(copy.deepcopy(grid))
                inspected = analyze(grid)
                expected_axes = {key: inspected[key] for key in AXIS_KEYS}
                if declared != expected_axes:
                    totals["observer_mismatches"] += 1
                    errors.append(
                        f"{label}: observe_overrides={declared!r}, independent={expected_axes!r}"
                    )
                profile = gen.schedule_profile(draw_seed, sample_index, difficulty=band)
                profile_counts[str(profile)] += 1
                band_counts[band][str(profile)] += 1
                for name, witness in gen.SEMANTIC_WITNESSES.items():
                    if witness(copy.deepcopy(grid)):
                        witness_counts[name] += 1
                        for rival_name in gen.WITNESS_RIVALS.get(name, []):
                            rival = gen.SEMANTIC_RIVALS[rival_name]
                            if rival(copy.deepcopy(grid)) != expected:
                                rival_disagreements[rival_name] += 1
                            else:
                                totals["false_witness_claims"] += 1
                                errors.append(
                                    f"{label}: witness {name!r} fired without refuting {rival_name!r}"
                                )
            except Exception as exc:
                totals["exceptions"] += 1
                errors.append(f"{label}: {type(exc).__name__}: {exc}")

    missing_witnesses = sorted(name for name, count in witness_counts.items() if count == 0)
    if missing_witnesses:
        errors.append(f"zero-support witnesses: {missing_witnesses}")
    missing_profiles = sorted(set(map(str, gen.SCHEDULE_PROFILES)) - set(profile_counts))
    if missing_profiles:
        errors.append(f"unvisited schedule profiles: {missing_profiles}")
    totals["unique_inputs"] = len(unique)
    return {
        **dict(totals),
        "draws": totals["draws"],
        "self_check_failures": totals["self_check_failures"],
        "strict_failures": totals["strict_failures"],
        "observer_mismatches": totals["observer_mismatches"],
        "rule_mirror_mismatches": totals["rule_mirror_mismatches"],
        "identity_outputs": totals["identity_outputs"],
        "unique_inputs": len(unique),
        "witness_counts": dict(witness_counts),
        "rival_disagreement_counts": dict(rival_disagreements),
        "schedule_profile_counts": dict(profile_counts),
        "per_band_profile_counts": {band: dict(counts) for band, counts in band_counts.items()},
        "errors": errors,
    }


def _override_check(gen, *, seed: int) -> dict[str, Any]:
    failures = 0
    errors: list[str] = []
    cases = 0
    for band_index, band in enumerate(BANDS):
        for case_index, options in enumerate(_OVERRIDE_CASES):
            cases += 1
            label = f"{band} case={case_index} {options}"
            try:
                grid = gen.generate(
                    seed + 10_000 + band_index * 100 + case_index,
                    97 + case_index,
                    difficulty=band,
                    **options,
                )
                independent = analyze(grid)
                declared = gen.observe_overrides(copy.deepcopy(grid))
                got = {key: independent[key] for key in AXIS_KEYS}
                findings = list(gen.self_check(copy.deepcopy(grid)) or [])
                if got != options or declared != options or findings:
                    failures += 1
                    errors.append(
                        f"{label}: independent={got!r}; declared={declared!r}; findings={findings!r}"
                    )
            except Exception as exc:
                failures += 1
                errors.append(f"{label}: {type(exc).__name__}: {exc}")
    return {"cases": cases, "failures": failures, "errors": errors}


def _lesson_check(gen, *, starts: int, seed: int) -> dict[str, Any]:
    rotations = 0
    unidentifiable = 0
    survivor_counts: Counter[str] = Counter({name: 0 for name in gen.LESSON_COMPETITORS})
    errors: list[str] = []
    for band_index, band in enumerate(BANDS):
        for start in range(starts):
            lesson_seed = seed + 50_000 + band_index * 1000 + start
            pairs = []
            for offset in range(4):
                grid = gen.generate(lesson_seed, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": independent_rule(grid)})
            for query_index, query in enumerate(pairs):
                rotations += 1
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                reasons, hook_error = _safe_reasons(gen, demos, query)
                label = f"{band} start={start} query={query_index}"
                if hook_error:
                    unidentifiable += 1
                    errors.append(f"{label}: lesson hook {hook_error}")
                elif reasons:
                    unidentifiable += 1
                    errors.append(f"{label}: {reasons}")
                for name, rival in gen.LESSON_COMPETITORS.items():
                    try:
                        survived = all(
                            rival(copy.deepcopy(pair["input"])) == pair["output"]
                            for pair in demos
                        )
                    except Exception as exc:
                        survived = True
                        errors.append(f"{label}: rival {name!r} raised {type(exc).__name__}: {exc}")
                    if survived:
                        survivor_counts[name] += 1
                        if not hook_error and not reasons:
                            unidentifiable += 1
                            errors.append(
                                f"{label}: rival {name!r} survives although hook returned identifiable"
                            )
    return {
        "starts_per_band": starts,
        "rotations": rotations,
        "unidentifiable_rotations": unidentifiable,
        "survivor_counts": dict(survivor_counts),
        "errors": errors,
    }


def qualify_generator(gen, *, per_band: int = 60, starts: int = 12, seed: int = 0) -> dict[str, Any]:
    """Run the task-specific source-only probe and return a JSON-safe report."""
    if type(per_band) is not int or per_band < 1:
        raise ValueError("per_band must be a positive integer")
    if type(starts) is not int or starts < 1:
        raise ValueError("starts must be a positive integer")
    source = Path(gen.__file__).resolve()
    canonical = _canonical_check(gen)
    population = _population_check(gen, per_band=per_band, seed=seed)
    overrides = _override_check(gen, seed=seed)
    lessons = _lesson_check(gen, starts=starts, seed=seed)
    errors = [
        *canonical["errors"],
        *population["errors"],
        *overrides["errors"],
        *lessons["errors"],
    ]
    return {
        "schema": "arc-horizontal-span-qualify-v1",
        "status": "PASS" if not errors else "FAIL",
        "generator": {
            "task_id": getattr(gen, "TASK_ID", None),
            "version": getattr(gen, "VERSION", None),
            "rule_hash": getattr(gen, "RULE_HASH", None),
            "source": str(source),
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        },
        "settings": {"per_band": per_band, "starts": starts, "seed": seed},
        "canonical": canonical,
        "population": population,
        "overrides": overrides,
        "lessons": lessons,
        "errors": errors,
        "limits": [
            "Source-only mirror check; run the repository battery for Racket authority parity.",
            "Finite declared-rival census, not a proof of unique induction.",
            "Exact-axis cases cover the declared extremes and teaching modes, not every Cartesian tuple.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, help="alternate generator.py under test")
    parser.add_argument("--per-band", type=int, default=60)
    parser.add_argument("--starts", type=int, default=12)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    gen = load_generator(args.generator)
    report = qualify_generator(gen, per_band=args.per_band, starts=args.starts, seed=args.seed)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    print(
        json.dumps(
            {
                "task_id": report["generator"]["task_id"],
                "status": report["status"],
                "draws": report["population"]["draws"],
                "unique_inputs": report["population"]["unique_inputs"],
                "rotations": report["lessons"]["rotations"],
                "errors": len(report["errors"]),
                "out": str(args.out) if args.out else None,
            },
            indent=2,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
