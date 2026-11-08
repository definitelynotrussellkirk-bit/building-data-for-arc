#!/usr/bin/env python3
"""Source-bound curriculum and lesson-identifiability probe for 80271cb9b303.

The probe deliberately reads the generator's own LESSON_COMPETITORS and
CANONICAL_SHORTCUTS declarations.  It checks the three-slot period contract,
all cyclic starts in that schedule, task validation, rival survival, and unique
input counts.  It does not execute the Racket authority; the normal battery is
responsible for rule parity.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


TASK_ID = "80271cb9b303"
EXPECTED_PERIODS = ({4}, {3}, {5, 6})


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_generator():
    repo = _repo_root()
    runtime = repo / "shared" / "runtime"
    if str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))
    path = repo / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(
        f"generator_{TASK_ID}_curriculum_probe", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _canonical_pairs() -> list[dict[str, Any]]:
    ledger = _repo_root() / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in ledger.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
            return [*row["train"], *tests]
    raise RuntimeError(f"canonical row {TASK_ID} not found")


def _canonical_shortcut_fit(gen) -> dict[str, Any]:
    pairs = _canonical_pairs()
    report: dict[str, Any] = {}
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        fits = 0
        errors: list[str] = []
        for index, pair in enumerate(pairs):
            try:
                if shortcut(pair["input"]) == pair["output"]:
                    fits += 1
            except Exception as exc:  # retained as evidence, never silently ignored
                errors.append(f"pair {index}: {type(exc).__name__}: {exc}")
        report[name] = {
            "fits_pairs": fits,
            "pair_count": len(pairs),
            "fits_all": fits == len(pairs) and not errors,
            "errors": errors,
        }
    return report


def probe_band(gen, band: str, seed_start: int, seeds: int) -> dict[str, Any]:
    slot_periods = [Counter() for _ in range(gen.EXAMPLES_NEEDED)]
    unique_inputs: set[str] = set()
    contract_failures: list[dict[str, Any]] = []
    self_check_failures: list[dict[str, Any]] = []
    lesson_failures: list[dict[str, Any]] = []
    harmful_survivors: list[dict[str, Any]] = []
    contract_failure_count = 0
    self_check_failure_count = 0
    lesson_failure_count = 0
    harmful_survival_count = 0
    survivor_counts: Counter[str] = Counter()
    harmful_counts: Counter[str] = Counter()
    start_counts: Counter[int] = Counter()

    for offset in range(seeds):
        seed = seed_start + offset
        base = offset * gen.EXAMPLES_NEEDED
        pairs: dict[int, dict[str, Any]] = {}

        # Six consecutive samples cover the base 3-slot cycle and all three
        # cyclic three-demo windows plus their following query.
        for sample_index in range(base, base + 2 * gen.EXAMPLES_NEEDED):
            grid = gen.generate(seed, sample_index, difficulty=band)
            unique_inputs.add(_grid_hash(grid))
            issues = gen.self_check(grid)
            if issues:
                self_check_failure_count += 1
                if len(self_check_failures) < 50:
                    self_check_failures.append(
                        {
                            "seed": seed,
                            "sample_index": sample_index,
                            "issues": issues,
                        }
                    )
            pairs[sample_index] = {"input": grid, "output": gen._solve_true(grid)}

        for slot in range(gen.EXAMPLES_NEEDED):
            sample_index = base + slot
            period = gen.observe_overrides(pairs[sample_index]["input"])["period"]
            slot_periods[slot][str(period)] += 1
            if period not in EXPECTED_PERIODS[slot]:
                contract_failure_count += 1
                if len(contract_failures) < 50:
                    contract_failures.append(
                        {
                            "seed": seed,
                            "sample_index": sample_index,
                            "slot": slot,
                            "period": period,
                            "expected": sorted(EXPECTED_PERIODS[slot]),
                        }
                    )

        for start_offset in range(gen.EXAMPLES_NEEDED):
            start = base + start_offset
            demos = [pairs[index] for index in range(start, start + gen.EXAMPLES_NEEDED)]
            query = pairs[start + gen.EXAMPLES_NEEDED]
            start_counts[start_offset] += 1
            reasons = gen.lesson_identifiable(demos, query)
            if reasons:
                lesson_failure_count += 1
                if len(lesson_failures) < 50:
                    lesson_failures.append(
                        {
                            "seed": seed,
                            "start_sample_index": start,
                            "cyclic_start": start_offset,
                            "reasons": reasons,
                        }
                    )

            true_answer = query["output"]
            for name, competitor in gen.LESSON_COMPETITORS.items():
                fits_demos = all(
                    competitor(pair["input"]) == pair["output"] for pair in demos
                )
                if not fits_demos:
                    continue
                survivor_counts[name] += 1
                if competitor(query["input"]) != true_answer:
                    harmful_counts[name] += 1
                    harmful_survival_count += 1
                    if len(harmful_survivors) < 50:
                        harmful_survivors.append(
                            {
                                "seed": seed,
                                "start_sample_index": start,
                                "cyclic_start": start_offset,
                                "competitor": name,
                            }
                        )

    slot_histograms = [dict(sorted(counter.items())) for counter in slot_periods]
    observed_long = set(slot_periods[2])
    long_period_diversity_ok = observed_long == {"5", "6"}
    total_generated = seeds * 2 * gen.EXAMPLES_NEEDED
    total_lessons = seeds * gen.EXAMPLES_NEEDED
    return {
        "band": band,
        "seed_range": [seed_start, seed_start + seeds - 1],
        "seeds": seeds,
        "sample_index_policy": (
            "for seed offset i, generate 6 consecutive samples beginning at 3*i; "
            "evaluate period slots 0..2 and lessons at cyclic starts 0,1,2"
        ),
        "generated_grid_count": total_generated,
        "unique_input_count": len(unique_inputs),
        "lesson_count": total_lessons,
        "lesson_start_counts": {str(k): v for k, v in sorted(start_counts.items())},
        "slot_period_histograms": slot_histograms,
        "long_period_diversity_ok": long_period_diversity_ok,
        "period_contract_failure_count": contract_failure_count,
        "period_contract_failures_first_50": contract_failures,
        "self_check_failure_count": self_check_failure_count,
        "self_check_failures_first_50": self_check_failures,
        "lesson_identifiability_failure_count": lesson_failure_count,
        "lesson_identifiability_failures_first_50": lesson_failures,
        "competitor_demo_survival_counts": dict(sorted(survivor_counts.items())),
        "harmful_competitor_survival_counts": dict(sorted(harmful_counts.items())),
        "harmful_competitor_survivors_first_50": harmful_survivors,
        "passed": (
            contract_failure_count == 0
            and self_check_failure_count == 0
            and lesson_failure_count == 0
            and harmful_survival_count == 0
            and long_period_diversity_ok
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=200)
    parser.add_argument("--seed-start", type=int, default=1000)
    parser.add_argument("--bands", default="easy,medium,hard")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.seeds <= 0:
        parser.error("--seeds must be positive")

    gen, generator_path = _load_generator()
    bands = [item.strip() for item in args.bands.split(",") if item.strip()]
    if not bands:
        parser.error("--bands must contain at least one band")

    band_reports = [probe_band(gen, band, args.seed_start, args.seeds) for band in bands]
    generator_sha256 = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    report = {
        "schema": "80271cb9b303-curriculum-probe-v1",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": generator_sha256,
        "rule_hash_declared": gen.RULE_HASH,
        "racket_executed": False,
        "expected_period_schedule": [[4], [3], [5, 6]],
        "lesson_assembly": (
            "same seed, consecutive sample indexes, three demos followed by one query; "
            "all cyclic starts 0, 1, and 2 are tested"
        ),
        "competitors_source": "generator.LESSON_COMPETITORS",
        "canonical_shortcuts_source": "generator.CANONICAL_SHORTCUTS",
        "canonical_shortcut_fit": _canonical_shortcut_fit(gen),
        "bands": band_reports,
        "totals": {
            "generated_grids": sum(item["generated_grid_count"] for item in band_reports),
            "unique_inputs_sum_across_bands": sum(
                item["unique_input_count"] for item in band_reports
            ),
            "lesson_windows": sum(item["lesson_count"] for item in band_reports),
            "period_contract_failures": sum(
                item["period_contract_failure_count"] for item in band_reports
            ),
            "self_check_failures": sum(
                item["self_check_failure_count"] for item in band_reports
            ),
            "lesson_identifiability_failures": sum(
                item["lesson_identifiability_failure_count"] for item in band_reports
            ),
            "harmful_competitor_survivals": sum(
                sum(item["harmful_competitor_survival_counts"].values())
                for item in band_reports
            ),
        },
        "passed": all(item["passed"] for item in band_reports),
        "limitations": [
            "This is a deterministic finite probe, not a universal induction guarantee.",
            "It uses the Python true solver and does not replace Racket rule-smoke/authority checks.",
            "Unique-input counts are per band; cross-band overlap is not subtracted from their sum.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(args.output), "passed": report["passed"], **report["totals"]}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
