"""Lesson-window and query-rotation probe for f361853c0fcd."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reference_probe import intended_output, load_generator


def _pair(grid):
    return {"input": grid, "output": intended_output(grid)}


def build_schedule_report(
    module=None,
    *,
    seeds=range(100),
    difficulties=("easy", "medium", "hard"),
):
    module = load_generator() if module is None else module
    window = int(module.EXAMPLES_NEEDED) + 1
    period = len(tuple(module.SCHEDULE_PROFILES))
    starts = list(range(period))
    competitors = dict(module.LESSON_COMPETITORS)
    counters = {"lessons": 0, "rotations": 0, "ambiguous_rotations": 0, "hook_failures": 0}
    per_band = {}
    counterexamples = []

    for difficulty in difficulties:
        band = {key: 0 for key in counters}
        for seed in seeds:
            for start in starts:
                lesson = [
                    _pair(module.generate(seed, start + offset, difficulty=difficulty))
                    for offset in range(window)
                ]
                counters["lessons"] += 1
                band["lessons"] += 1
                for query_index in range(window):
                    counters["rotations"] += 1
                    band["rotations"] += 1
                    query = lesson[query_index]
                    demos = lesson[:query_index] + lesson[query_index + 1 :]
                    reasons = list(module.lesson_identifiable(demos, query))
                    if reasons:
                        counters["hook_failures"] += 1
                        band["hook_failures"] += 1
                    ambiguous = [
                        name
                        for name, rival in competitors.items()
                        if all(rival(pair["input"]) == pair["output"] for pair in demos)
                        and rival(query["input"]) != query["output"]
                    ]
                    if ambiguous:
                        counters["ambiguous_rotations"] += 1
                        band["ambiguous_rotations"] += 1
                    if (reasons or ambiguous) and len(counterexamples) < 20:
                        counterexamples.append(
                            {
                                "difficulty": difficulty,
                                "seed": seed,
                                "start": start,
                                "query_index": query_index,
                                "hook_reasons": reasons,
                                "ambiguous_competitors": ambiguous,
                                "lesson": lesson,
                            }
                        )
        per_band[difficulty] = band

    source = Path(module.__file__).resolve()
    return {
        "schema": "arc-task-schedule-probe-v1",
        "task_id": module.TASK_ID,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "rule_hash": module.RULE_HASH,
        "authority": "independent_python_oracle_not_racket",
        "period": period,
        "window": window,
        "starts": starts,
        "seeds": list(seeds),
        "difficulties": list(difficulties),
        "competitors": sorted(competitors),
        "summary": counters,
        "per_band": per_band,
        "counterexamples": counterexamples,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator")
    parser.add_argument("--seeds", type=int, default=100)
    parser.add_argument("--difficulty", action="append", choices=("easy", "medium", "hard"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = build_schedule_report(
        load_generator(args.generator),
        seeds=range(args.seeds),
        difficulties=args.difficulty or ("easy", "medium", "hard"),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(args.out)
    if report["summary"]["ambiguous_rotations"] or report["summary"]["hook_failures"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
