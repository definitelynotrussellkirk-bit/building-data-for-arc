#!/usr/bin/env python3
"""Exhaustively verify the finite teaching schedule for d5a059b0f3a6."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import find_root, load_selected_generator

TASK_ID = "d5a059b0f3a6"
BANDS = (None, "easy", "medium", "hard")


def digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def verify(seed: int) -> dict[str, Any]:
    root = find_root(__file__)
    gen, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    rows = []
    failures = []
    for band in BANDS:
        for start in range(gen.SCHEDULE_PERIOD):
            pairs = []
            for offset in range(4):
                sample_index = start + offset
                grid = gen.generate(seed, sample_index, difficulty=band)
                reasons = gen.self_check(grid)
                observed = gen.observe_overrides(grid)["scene_profile"]
                scheduled = gen.schedule_profile(seed, sample_index, band)
                if reasons:
                    failures.append(
                        f"band={band!r} start={start} offset={offset}: {reasons}"
                    )
                if observed != scheduled:
                    failures.append(
                        f"band={band!r} sample={sample_index}: observed "
                        f"{observed!r} != scheduled {scheduled!r}"
                    )
                pairs.append(
                    {
                        "input": grid,
                        "output": gen.solve_python(grid),
                        "profile": observed,
                        "input_sha256": digest(grid),
                    }
                )

            rotations = []
            for query_offset in range(4):
                query = pairs[query_offset]
                demos = [
                    {"input": pair["input"], "output": pair["output"]}
                    for offset, pair in enumerate(pairs)
                    if offset != query_offset
                ]
                query_pair = {
                    "input": query["input"],
                    "output": query["output"],
                }
                hook_reasons = gen.lesson_identifiable(
                    deepcopy(demos), deepcopy(query_pair)
                )
                rival_status = {}
                for name, rival in gen.LESSON_COMPETITORS.items():
                    survives = all(
                        rival(pair["input"]) == pair["output"]
                        for pair in demos
                    )
                    changes_query = rival(query["input"]) != query["output"]
                    rival_status[name] = {
                        "survives_demos": survives,
                        "changes_query": changes_query,
                        "ambiguous": survives and changes_query,
                    }
                    if survives and changes_query:
                        failures.append(
                            f"band={band!r} start={start} query={query_offset}: "
                            f"{name} remains ambiguous"
                        )
                if hook_reasons:
                    failures.append(
                        f"band={band!r} start={start} query={query_offset}: "
                        f"hook={hook_reasons}"
                    )
                rotations.append(
                    {
                        "query_offset": query_offset,
                        "hook_reasons": hook_reasons,
                        "rivals": rival_status,
                    }
                )
            rows.append(
                {
                    "band": band,
                    "start": start,
                    "profiles": [pair["profile"] for pair in pairs],
                    "input_sha256": [pair["input_sha256"] for pair in pairs],
                    "rotations": rotations,
                }
            )

    report = {
        "schema": "d5a059b0f3a6-teaching-schedule-v1",
        "status": "passed" if not failures else "failed",
        "task_id": TASK_ID,
        "seed": seed,
        "generator_source": str(source_path.relative_to(root)),
        "generator_sha256": source_sha256,
        "schedule_period": gen.SCHEDULE_PERIOD,
        "default_profile_schedule": list(gen.DEFAULT_PROFILE_SCHEDULE),
        "bands": list(BANDS),
        "windows_checked": len(rows),
        "rotations_checked": sum(len(row["rotations"]) for row in rows),
        "declared_rivals": sorted(gen.LESSON_COMPETITORS),
        "failures": failures,
        "rows": rows,
        "scope": (
            "Exhaustive over every cyclic schedule start, four difficulty calls, "
            "and every one-query rotation for one deterministic seed; finite "
            "declared-rival evidence, not universal induction."
        ),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=109)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = verify(args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "windows_checked": report["windows_checked"],
        "rotations_checked": report["rotations_checked"],
        "out": str(args.out),
    }, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
