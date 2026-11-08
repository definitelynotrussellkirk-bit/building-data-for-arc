"""Exhaustive cyclic-start and query-rotation probe for task 1a92a12bac06.

The production schedule has period four.  This tool checks every cyclic start
for supplied seeds/bands, holds out each pair once, and evaluates the generator's
own declared lesson hook and competitors against an independent Python oracle.
It is diagnostic evidence, not Racket label authority.
"""
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
    seeds = tuple(int(seed) for seed in seeds)
    difficulties = tuple(difficulties)
    period = len(tuple(module.SCHEDULE_PROFILES))
    starts = list(range(period))
    competitors = dict(module.LESSON_COMPETITORS)

    lessons = 0
    rotations = 0
    ambiguous_rotations = 0
    hook_failures = 0
    counterexamples = []
    profile_sequences = {}
    per_band = {}

    for difficulty in difficulties:
        band_lessons = 0
        band_rotations = 0
        band_ambiguous = 0
        band_hooks = 0
        for seed in seeds:
            for start in starts:
                lesson = [
                    _pair(module.generate(seed, start + offset, difficulty=difficulty))
                    for offset in range(period)
                ]
                sequence = tuple(
                    module.schedule_profile(seed, start + offset, difficulty=difficulty)
                    for offset in range(period)
                )
                profile_sequences.setdefault(str(start), list(sequence))
                lessons += 1
                band_lessons += 1
                for query_index in range(period):
                    rotations += 1
                    band_rotations += 1
                    query = lesson[query_index]
                    demos = lesson[:query_index] + lesson[query_index + 1 :]
                    reasons = list(module.lesson_identifiable(demos, query))
                    if reasons:
                        hook_failures += 1
                        band_hooks += 1
                    ambiguous = []
                    for name, competitor in competitors.items():
                        fits = all(
                            competitor(pair["input"]) == pair["output"]
                            for pair in demos
                        )
                        changes_query = (
                            competitor(query["input"]) != query["output"]
                        )
                        if fits and changes_query:
                            ambiguous.append(name)
                    if reasons or ambiguous:
                        if ambiguous:
                            ambiguous_rotations += 1
                            band_ambiguous += 1
                        if len(counterexamples) < 20:
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
        per_band[difficulty] = {
            "lessons": band_lessons,
            "rotations": band_rotations,
            "ambiguous_rotations": band_ambiguous,
            "hook_failures": band_hooks,
        }

    source = Path(module.__file__).resolve()
    return {
        "schema": "arc-task-schedule-probe-v1",
        "task_id": getattr(module, "TASK_ID", "1a92a12bac06"),
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "rule_hash": getattr(module, "RULE_HASH", None),
        "authority": "independent_python_oracle_not_racket",
        "period": period,
        "starts": starts,
        "seeds": list(seeds),
        "difficulties": list(difficulties),
        "competitors": sorted(competitors),
        "profile_sequences": profile_sequences,
        "summary": {
            "lessons": lessons,
            "rotations": rotations,
            "ambiguous_rotations": ambiguous_rotations,
            "hook_failures": hook_failures,
        },
        "per_band": per_band,
        "counterexamples": counterexamples,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=100, help="check seeds 0..N-1")
    parser.add_argument(
        "--difficulty",
        action="append",
        choices=("easy", "medium", "hard"),
        help="repeat to restrict bands; default checks all three",
    )
    parser.add_argument("--generator", help="alternate generator.py path")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    module = load_generator(args.generator)
    report = build_schedule_report(
        module,
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
