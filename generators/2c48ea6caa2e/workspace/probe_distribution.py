#!/usr/bin/env python3
"""Report deterministic duplicate concentration by schedule/profile branch."""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import json

from reviewer_support import find_root, load_selected_generator

TASK_ID = "2c48ea6caa2e"
ROOT = find_root(__file__)
GEN, SOURCE, SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def frozen(grid):
    return json.dumps(grid, separators=(",", ":"))


def main():
    report = {"task_id": TASK_ID, "source": str(SOURCE), "sha256": SHA256, "cases": []}
    for start in (0, 50_000):
        for band_index, band in enumerate(("easy", "medium", "hard")):
            seen = defaultdict(list)
            branches = Counter()
            details = Counter()
            for offset in range(300):
                seed = start + 10_000 * band_index + offset
                sample_index = seed * 29 + 7
                grid = GEN.generate(seed, sample_index, difficulty=band)
                observed = GEN.observe_overrides(grid)
                branch = GEN.schedule_profile(seed, sample_index, band)
                branches[branch] += 1
                details[(branch, observed["scene_profile"], observed["padding_profile"])] += 1
                seen[frozen(grid)].append({
                    "seed": seed,
                    "sample_index": sample_index,
                    "branch": branch,
                    **observed,
                })
            duplicate_groups = [rows for rows in seen.values() if len(rows) > 1]
            report["cases"].append({
                "start": start,
                "band": band,
                "unique": len(seen),
                "duplicates": sum(len(rows) - 1 for rows in duplicate_groups),
                "duplicate_groups": duplicate_groups[:20],
                "branches": dict(branches),
                "details": {"|".join(key): value for key, value in sorted(details.items())},
            })
    out = Path(__file__).with_name("distribution_probe.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(out)
    for case in report["cases"]:
        print(case["start"], case["band"], case["unique"], case["duplicates"])


if __name__ == "__main__":
    main()
