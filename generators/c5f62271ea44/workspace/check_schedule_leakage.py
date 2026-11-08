"""Source-bound probe for a lesson-level schedule/blue-corner shortcut.

From the packet root:
  python3 review.py run ../.venv/bin/python \
    generators/c5f62271ea44/workspace/check_schedule_leakage.py \
    --seed-count 256 --out ../checks/schedule-leakage

The lookup is given the known held-out position, all four ordered demonstration
transform names, and the query's actual source/target blue-corner positions. If
the same lookup key requires two different query transforms, this information
alone cannot solve every observed lesson. This is a finite projected-information
check, not universal identifiability or a measured model score. It executes the
generator, not Racket; witness-inputs.json is suitable for arcpuzzles apply.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator


TASK_ID = "c5f62271ea44"


def run(seed_count: int, out: Path) -> dict:
    if type(seed_count) is not int or seed_count < 1:
        raise ValueError("seed_count must be a positive integer")
    if out.exists():
        raise FileExistsError(out)
    root = find_root(__file__)
    gen, source, source_hash = load_selected_generator(TASK_ID, root=root)
    period = gen.LESSON_SCHEDULE_PERIOD
    buckets = {}
    class_patterns = Counter()
    generated_inputs = 0
    quarters = {"rot_cw", "rot_ccw"}
    diagonal = {"transpose", "anti_transpose"}
    swapping = quarters | diagonal
    for seed in range(seed_count):
        order = [gen.schedule_profile(seed, i) for i in range(period)]
        assert set(order) == set(gen.SYMMETRIES), (seed, "missing transform")
        class_patterns["".join("Q" if t in quarters else "D" if t in diagonal else "O"
                               for t in order)] += 1
        queries = []
        for index in range(period + 4):
            grid = gen.generate(seed, index, difficulty="medium")
            analysis = gen._analyze(grid)
            assert not analysis["errors"], (seed, index, analysis["errors"])
            assert analysis["symmetry"] == order[index % period]
            queries.append((grid, analysis["corners"].index(1), analysis["signature"].index(1)))
            generated_inputs += 1
        for start in range(period):
            window = [order[(start + j) % period] for j in range(5)]
            for held_out in range(5):
                demos = tuple(window[:held_out] + window[held_out + 1:])
                assert len(set(demos)) >= 3
                assert set(demos) & quarters
                assert set(demos) & swapping and set(demos) - swapping
                query_index = start + held_out
                grid, blue_source, blue_target = queries[query_index]
                key = (held_out, demos, blue_source, blue_target)
                bucket = buckets.setdefault(key, {"count": 0, "by_transform": {}})
                bucket["count"] += 1
                bucket["by_transform"].setdefault(window[held_out], {
                    "seed": seed, "start": start, "sample_index": query_index,
                    "held_out_position": held_out, "difficulty": "medium",
                    "ordered_demo_transforms": list(demos), "cycle": order,
                    "source_blue_corner": blue_source, "target_blue_corner": blue_target,
                    "query_transform": window[held_out], "input": grid,
                })
    summaries = []
    witnesses = []
    inputs = []
    for held_out in range(5):
        selected = [(key, value) for key, value in buckets.items() if key[0] == held_out]
        ambiguous = [(key, value) for key, value in selected if len(value["by_transform"]) > 1]
        events = sum(value["count"] for _, value in selected)
        ambiguous_events = sum(value["count"] for _, value in ambiguous)
        summaries.append({"held_out_position": held_out, "events": events,
                          "keys": len(selected), "ambiguous_keys": len(ambiguous),
                          "events_in_ambiguous_keys": ambiguous_events,
                          "observed_ambiguous_event_fraction": ambiguous_events / events})
        if ambiguous:
            key, value = ambiguous[0]
            pair = list(value["by_transform"].values())[:2]
            rows = []
            for witness in pair:
                row = {k: v for k, v in witness.items() if k != "input"}
                row["racket_input_index"] = len(inputs)
                inputs.append(witness["input"])
                rows.append(row)
            witnesses.append({"held_out_position": held_out,
                              "same_projection_different_query_transforms": rows})
    report = {"schema": "c5f62271ea44-schedule-leakage-v1", "task_id": TASK_ID,
              "generator_sha256": source_hash, "generator_path": str(source),
              "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "generator_version": gen.VERSION, "schedule_period": period,
              "seed_range": [0, seed_count - 1], "generated_inputs": generated_inputs,
              "lessons": seed_count * period, "holdout_events": seed_count * period * 5,
              "distinct_class_patterns_observed": len(class_patterns),
              "by_holdout": summaries, "witnesses": witnesses,
              "racket_executions": 0,
              "status": ("lookup_refuted_at_every_holdout" if len(witnesses) == 5
                         else "some_holdouts_have_no_observed_collision"),
              "limits": ["Actual generated queries and seeded schedules; no Racket labels in this probe.",
                         "A projection collision refutes only the specified information-limited lookup.",
                         "No observed collision is not evidence of complete predictability.",
                         "Fractions describe this bounded cohort, not all seeds or a trained solver.",
                         "Partial schedule information and other undeclared shortcuts may remain."]}
    out.mkdir(parents=True)
    (out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    (out / "witness-inputs.json").write_text(json.dumps(inputs, indent=2) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-count", type=int, default=256)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.seed_count, args.out)
    print(json.dumps({k: report[k] for k in ("status", "generator_sha256", "lessons",
                                            "holdout_events", "generated_inputs", "by_holdout")}))
    if report["status"] != "lookup_refuted_at_every_holdout":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
