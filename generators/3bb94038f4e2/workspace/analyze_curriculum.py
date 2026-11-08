#!/usr/bin/env python3
"""Source-bound curriculum audit for 3bb94038f4e2.

This complements the production lesson census with a cheap, exhaustive check of
consecutive schedule starts and every possible held-out query position.  It uses
an independent Python oracle for diagnostics; Racket remains label authority.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from reference_probe import (
    canonical_pairs,
    intended_output,
    load_generator,
    normalized_rule_hash,
    profile,
    semantic_features,
)

BANDS = ("easy", "medium", "hard")


def _seed(label: str) -> int:
    return int(hashlib.sha256(label.encode()).hexdigest()[:12], 16)


def _digest(grid) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _counter_dict(counter):
    return {str(key): value for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def analyze(module, *, per_band: int = 100, cyclic_starts: int = 12):
    if per_band < 1 or cyclic_starts < 1:
        raise ValueError("per_band and cyclic_starts must be positive")
    canonical_profiles = {profile(pair["input"]) for pair in canonical_pairs()}
    report = {
        "schema": "3bb94038f4e2-curriculum-audit-v1",
        "task_id": "3bb94038f4e2",
        "version": module.VERSION,
        "declared_rule_hash": getattr(module, "RULE_HASH", None),
        "canonical_rule_hash": normalized_rule_hash(),
        "sampler": {
            "per_band": per_band,
            "cyclic_starts": cyclic_starts,
            "bands": list(BANDS),
            "draw_seed": "sha256('3bb94038f4e2:audit:BAND:INDEX')[:12]",
            "cyclic_seed": "sha256('3bb94038f4e2:cycle:BAND:START')[:12]",
            "lesson_shape": "three demos plus one query; every query rotation",
        },
        "per_band": {},
        "totals": {},
        "limits": [
            "Finite declared-rival analysis is not a proof of universal identifiability.",
            "The independent Python oracle is diagnostic evidence, not label authority.",
            "The production lesson census separately validates materialization and Racket labels.",
        ],
    }
    totals = Counter()
    failures = []
    for band in BANDS:
        counts = Counter()
        profiles = Counter()
        shapes = Counter()
        witnesses = Counter()
        rival_disagreements = Counter()
        unique_inputs = set()
        unique_outputs = set()
        exact_hits = 0
        for index in range(per_band):
            seed = _seed(f"3bb94038f4e2:audit:{band}:{index}")
            grid = module.generate(seed, index, difficulty=band)
            counts["draws"] += 1
            counts["self_check_errors"] += bool(module.self_check(grid))
            counts["nondeterministic"] += grid != module.generate(seed, index, difficulty=band)
            expected = intended_output(grid)
            counts["identity_outputs"] += expected == grid
            counts["strict"] += not module.strict_canonical_like(grid)
            exact_hits += profile(grid) in canonical_profiles
            name = module.schedule_profile(seed, index, difficulty=band)
            profiles[name] += 1
            shapes[f"{len(grid)}x{len(grid[0])}"] += 1
            unique_inputs.add(_digest(grid))
            unique_outputs.add(_digest(expected))
            for feature, values in semantic_features(grid).items():
                witnesses[feature] += bool(values)
            for name, rival in module.LESSON_COMPETITORS.items():
                rival_disagreements[name] += rival(grid) != expected
            if module.schedule_profile(seed, index, difficulty=band) == "broad":
                missing = [
                    name
                    for name, values in semantic_features(grid).items()
                    if name in {
                        "wide_gaps",
                        "vertical_gaps",
                        "other_color_gaps",
                        "protected_centers",
                    }
                    and not values
                ]
                if missing:
                    failures.append(f"{band} draw {index}: broad profile missing {missing}")
                if len(semantic_features(grid)["true_gaps"]) < 2:
                    failures.append(f"{band} draw {index}: broad profile has fewer than two true gaps")

        cyclic = Counter()
        survivors = Counter()
        for start in range(cyclic_starts):
            seed = _seed(f"3bb94038f4e2:cycle:{band}:{start}")
            pairs = []
            for offset in range(4):
                grid = module.generate(seed, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": intended_output(grid)})
            for query_index in range(4):
                cyclic["cyclic_rotations"] += 1
                query = pairs[query_index]
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                hook_reasons = module.lesson_identifiable(demos, query)
                cyclic["cyclic_hook_warnings"] += bool(hook_reasons)
                ambiguous = False
                for name, rival in module.LESSON_COMPETITORS.items():
                    fits = all(rival(d["input"]) == d["output"] for d in demos)
                    changes_query = rival(query["input"]) != query["output"]
                    if fits:
                        survivors[name] += 1
                    if fits and changes_query:
                        ambiguous = True
                cyclic["cyclic_ambiguous_rotations"] += ambiguous
                if hook_reasons or ambiguous:
                    failures.append(
                        f"{band} start {start} query {query_index}: "
                        f"hook={hook_reasons!r} ambiguous={ambiguous}"
                    )

        band_row = {
            **dict(counts),
            **dict(cyclic),
            "canonical_exact_hits": exact_hits,
            "profiles": _counter_dict(profiles),
            "shapes": _counter_dict(shapes),
            "witness_draws": _counter_dict(witnesses),
            "rival_disagreements": _counter_dict(rival_disagreements),
            "cyclic_survivors": _counter_dict(survivors),
            "unique_inputs": len(unique_inputs),
            "unique_outputs": len(unique_outputs),
        }
        report["per_band"][band] = band_row
        totals.update(counts)
        totals.update(cyclic)
        totals["canonical_exact_hits"] += exact_hits
        totals["unique_inputs_sum_by_band"] += len(unique_inputs)
        totals["unique_outputs_sum_by_band"] += len(unique_outputs)
        if exact_hits == 0:
            failures.append(f"{band}: no exact canonical profile hit")
        if set(profiles) != set(module.SCHEDULE_PROFILES):
            failures.append(f"{band}: observed schedule profiles {sorted(profiles)}")
        if any(value == 0 for value in rival_disagreements.values()):
            failures.append(f"{band}: a declared rival never disagreed: {dict(rival_disagreements)}")

    report["totals"] = dict(totals)
    report["failures"] = failures
    report["status"] = "pass" if not failures and not any(
        totals[key]
        for key in (
            "self_check_errors",
            "nondeterministic",
            "identity_outputs",
            "cyclic_hook_warnings",
            "cyclic_ambiguous_rotations",
        )
    ) else "fail"
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--cyclic-starts", type=int, default=12)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    module = load_generator(args.generator)
    report = analyze(module, per_band=args.per_band, cyclic_starts=args.cyclic_starts)
    generator_path = Path(args.generator or Path(__file__).resolve().parents[1] / "generator.py")
    report["generator_sha256"] = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "totals": report["totals"]}, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
