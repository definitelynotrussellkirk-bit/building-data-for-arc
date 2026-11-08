#!/usr/bin/env python3
"""Cheap source-local curriculum probe for 395201c95f9d.

It checks every cyclic start of the 16-step schedule in every difficulty
band, scores the generator's declared lesson competitors, and confirms the
query never reuses the matching prototype's exact local coordinates.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "395201c95f9d"
GEN_PATH = Path(__file__).resolve().parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", GEN_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def pair(seed: int, sample_index: int, band: str) -> dict:
    grid = GEN.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def main() -> int:
    source_sha = hashlib.sha256(GEN_PATH.read_bytes()).hexdigest()
    rows = []
    failures = []
    for band in ("easy", "medium", "hard"):
        for start in range(len(GEN.SCHEDULE_PROFILES)):
            demos = [
                pair(910_000 + start, start + i, band)
                for i in range(GEN.EXAMPLES_NEEDED)
            ]
            query = pair(
                910_000 + start,
                start + GEN.EXAMPLES_NEEDED,
                band,
            )
            survivors = [
                name
                for name, rival in GEN.LESSON_COMPETITORS.items()
                if all(rival(d["input"]) == d["output"] for d in demos)
            ]
            hook_errors = GEN.lesson_identifiable(demos, query)
            row = {
                "band": band,
                "cyclic_start": start,
                "match_panels": sorted(
                    {
                        GEN.semantic_observables(d["input"])["matched_panel"]
                        for d in demos
                    }
                ),
                "surviving_rivals": survivors,
                "hook_errors": hook_errors,
            }
            rows.append(row)
            if survivors or hook_errors:
                failures.append(row)

    exact_pose_reuse = []
    schedule_hits = set()
    for band in ("easy", "medium", "hard"):
        for index in range(128):
            grid = GEN.generate(920_000 + index, index, difficulty=band)
            facts = GEN.semantic_observables(grid)
            schedule_hits.add(tuple(GEN.schedule_profile(920_000 + index, index, band)))
            panel = facts["matched_panel"]
            if facts["query_raw_cells"] == facts["prototype_raw_cells"][panel]:
                exact_pose_reuse.append({"band": band, "sample_index": index})

    output = {
        "schema": "395201c95f9d-lesson-probe-v1",
        "generator_sha256": source_sha,
        "lessons_checked": len(rows),
        "cyclic_starts_per_band": len(GEN.SCHEDULE_PROFILES),
        "declared_rivals": sorted(GEN.LESSON_COMPETITORS),
        "failures": failures,
        "exact_pose_reuse": exact_pose_reuse,
        "schedule_profiles_seen": sorted(repr(item) for item in schedule_hits),
        "schedule_profiles_expected": sorted(repr(item) for item in GEN.SCHEDULE_PROFILES),
        "rows": rows,
        "status": "PASS"
        if not failures
        and not exact_pose_reuse
        and schedule_hits == set(GEN.SCHEDULE_PROFILES)
        else "FAIL",
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
