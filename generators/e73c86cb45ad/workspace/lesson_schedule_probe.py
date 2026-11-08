"""Exhaust every cyclic default-schedule start against declared lesson rivals."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path

from reference_probe import first_candidate_output, load_generator, rule_output

HOME = Path(__file__).resolve().parents[1]


def schedule_period(module) -> int:
    # Size/distractor schedule repeats after 2*len(_SIZE_SCHEDULE); shape/rotation
    # after 16; match order after 3.  This is source-bound to the reviewed module.
    return math.lcm(2 * len(module._SIZE_SCHEDULE), 16, len(module._ORDER_SCHEDULE))


def audit(module):
    period = schedule_period(module)
    bands = (None, "easy", "medium", "hard")
    report = {
        "schema": "e73c86cb45ad-lesson-schedule-audit-v1",
        "generator_sha256": hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest(),
        "period": period,
        "demos_per_lesson": module.EXAMPLES_NEEDED,
        "query_policy": "next production sample after three ordered demos",
        "bands": {},
    }
    for band in bands:
        failures = []
        unique = set()
        witness_counts = [0, 0, 0]
        for start in range(period):
            grids = [
                module.generate(20261007 + start, start + offset, difficulty=band)
                for offset in range(4)
            ]
            for grid in grids:
                unique.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            demos = [{"input": grid, "output": rule_output(grid)} for grid in grids[:3]]
            query = {"input": grids[3], "output": rule_output(grids[3])}
            reasons = module.lesson_identifiable(deepcopy(demos), deepcopy(query))
            for index, grid in enumerate(grids[:3]):
                witness_counts[index] += first_candidate_output(grid) != rule_output(grid)
            if reasons:
                failures.append({"start": start, "reasons": reasons})
        report["bands"][str(band)] = {
            "starts_checked": period,
            "failures": failures,
            "unique_materialized_inputs": len(unique),
            "first_candidate_refuting_demo_counts_by_position": witness_counts,
        }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    module = load_generator(args.generator)
    result = audit(module)
    result["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "period": result["period"],
        "bands": {
            band: {"starts": row["starts_checked"], "failures": len(row["failures"]),
                   "unique_inputs": row["unique_materialized_inputs"],
                   "witness_positions": row["first_candidate_refuting_demo_counts_by_position"]}
            for band, row in result["bands"].items()
        },
    }, indent=2))
    return int(any(row["failures"] for row in result["bands"].values()))


if __name__ == "__main__":
    raise SystemExit(main())
