"""Exhaust the reviewed generator's current ten-slot lesson-start schedule.

This is reviewer evidence, not a public schedule contract.  It materializes
three demonstrations and one query at every start residue, checks the
independent row/column-count oracle, and verifies that every declared lesson
competitor is refuted by at least one demonstration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reference_probe import load_generator, output


def run(*, seeds: range = range(10)) -> dict:
    gen = load_generator()
    source = Path(gen.__file__).resolve()
    period = int(gen._SCHEDULE_PERIOD)
    demo_count = int(gen.EXAMPLES_NEEDED)
    bands = ("easy", "medium", "hard")
    records = []
    failures = []

    for band in bands:
        for seed in seeds:
            for start in range(period):
                pairs = []
                for sample_index in range(start, start + demo_count + 1):
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    errors = gen.self_check(grid)
                    pair = {"input": grid, "output": output(grid)}
                    pairs.append(pair)
                    if errors:
                        failures.append({
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "sample_index": sample_index,
                            "kind": "self_check",
                            "errors": errors,
                        })
                demos, query = pairs[:demo_count], pairs[demo_count]
                hook_warnings = list(gen.lesson_identifiable(demos, query))
                competitor_fits = {
                    name: all(predict(pair["input"]) == pair["output"] for pair in demos)
                    for name, predict in gen.LESSON_COMPETITORS.items()
                }
                record = {
                    "band": band,
                    "seed": seed,
                    "start_residue": start,
                    "sample_indices": list(range(start, start + demo_count + 1)),
                    "profiles": [
                        gen.observe_overrides(pair["input"])["profile_mode"]
                        for pair in pairs
                    ],
                    "hook_warnings": hook_warnings,
                    "competitor_fits_all_demos": competitor_fits,
                }
                records.append(record)
                if hook_warnings or any(competitor_fits.values()):
                    failures.append({"kind": "lesson", **record})

    return {
        "schema": "arc-review-schedule-probe-v1",
        "task_id": gen.TASK_ID,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "rule_hash": gen.RULE_HASH,
        "implementation_period": period,
        "public_period_declared": hasattr(gen, "LESSON_SCHEDULE_PERIOD"),
        "demo_count": demo_count,
        "bands": list(bands),
        "seed_range": [seeds.start, seeds.stop - 1],
        "lesson_count": len(records),
        "competitors": sorted(gen.LESSON_COMPETITORS),
        "failures": failures,
        "status": "pass" if not failures else "fail",
        "records": records,
        "limitations": (
            "Exhausts all ten current start residues for seeds 0..9 in each band; "
            "it is task-local evidence, not a public schedule-period contract or proof for all seeds."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "status": report["status"],
        "lesson_count": report["lesson_count"],
        "failures": len(report["failures"]),
        "generator_sha256": report["generator_sha256"],
    }))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
