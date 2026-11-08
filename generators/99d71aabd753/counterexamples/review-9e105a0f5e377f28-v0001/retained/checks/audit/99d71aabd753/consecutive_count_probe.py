from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import json

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "99d71aabd753"
ROOT = find_root(Path.cwd())
GEN, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def component_counts(grid: list[list[int]]) -> dict[int, int]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    counts: dict[int, int] = defaultdict(int)
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            counts[color] += 1
            seen.add((r, c))
            stack = [(r, c)]
            while stack:
                rr, cc = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
    return dict(counts)


def intended_output(grid: list[list[int]]) -> list[list[int]]:
    entries = sorted(component_counts(grid).items(), key=lambda item: item[1], reverse=True)
    width = entries[0][1]
    return [
        [0] * (width - count) + [color] * count
        for color, count in entries
    ]


def consecutive_length_rival(grid: list[list[int]]) -> list[list[int]]:
    """Sort correctly, but infer row lengths as max, max-1, ... by rank."""
    entries = sorted(component_counts(grid).items(), key=lambda item: item[1], reverse=True)
    width = entries[0][1]
    return [
        [0] * rank + [color] * (width - rank)
        for rank, (color, _actual_count) in enumerate(entries)
    ]


sample_rows = []
all_match = True
all_consecutive = True
for band in ("easy", "medium", "hard"):
    match_count = 0
    consecutive_count = 0
    profiles: set[tuple[int, ...]] = set()
    for seed in range(100):
        grid = GEN.generate(seed, seed * 101 + 17, difficulty=band)
        values = sorted(component_counts(grid).values(), reverse=True)
        profiles.add(tuple(values))
        is_consecutive = values == list(range(values[0], values[0] - len(values), -1))
        rival_matches = consecutive_length_rival(grid) == intended_output(grid)
        consecutive_count += int(is_consecutive)
        match_count += int(rival_matches)
        all_consecutive &= is_consecutive
        all_match &= rival_matches
    sample_rows.append(
        {
            "band": band,
            "draws": 100,
            "consecutive_profiles": consecutive_count,
            "rival_matches_intended": match_count,
            "observed_count_profiles": [list(profile) for profile in sorted(profiles)],
        }
    )

canonical_rows = []
counterexample = None
for index, pair in enumerate(canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)):
    counts = component_counts(pair["input"])
    intended = intended_output(pair["input"])
    rival = consecutive_length_rival(pair["input"])
    row = {
        "canonical_index": index,
        "split": pair["split"],
        "pair_index": pair["pair_index"],
        "component_counts": counts,
        "sorted_counts": sorted(counts.values(), reverse=True),
        "rival_matches_canonical": rival == pair["output"],
        "independent_intended_matches_canonical": intended == pair["output"],
    }
    canonical_rows.append(row)
    if counterexample is None and rival != pair["output"]:
        counterexample = {
            **row,
            "input": pair["input"],
            "canonical_output": pair["output"],
            "rival_output": rival,
        }

assert all_consecutive
assert all_match
assert counterexample is not None
assert all(row["independent_intended_matches_canonical"] for row in canonical_rows)

report = {
    "schema": "arc-audit-consecutive-count-shortcut-v1",
    "task_id": TASK_ID,
    "generator_source": str(SOURCE_PATH.relative_to(ROOT)),
    "generator_sha256": SOURCE_SHA256,
    "rule_hash": getattr(GEN, "RULE_HASH", None),
    "generated_sample": {
        "seed_range": [0, 99],
        "sample_index_formula": "seed * 101 + 17",
        "total_draws": 300,
        "all_component_count_profiles_consecutive": all_consecutive,
        "rival_matches_intended": all_match,
        "bands": sample_rows,
    },
    "canonical_pairs": canonical_rows,
    "counterexample": counterexample,
    "finding": (
        "The generator always uses consecutive component counts. A rival that sorts colors "
        "by the true count but emits max,max-1,... row lengths fits all 300 generated draws, "
        "yet fails canonical pairs whose actual counts have gaps."
    ),
}
print(json.dumps(report, indent=2, sort_keys=True))
