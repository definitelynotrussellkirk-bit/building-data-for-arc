#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator, normalize_grid

TASK_ID = "c2badae666ad"
ROOT = find_root(__file__)
OUT = Path(__file__).resolve().parent


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized_cells(grid, color):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
    if not cells:
        return set()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return {(r - r0, c - c0) for r, c in cells}


def exact2_output(grid, colors):
    sets = [normalized_cells(grid, color) for color in colors]
    union = set().union(*sets) if sets else set()
    exact2 = {p for p in union if sum(p in cells for cells in sets) == 2}
    if not exact2:
        return [[0]]
    r0 = min(r for r, _ in exact2)
    c0 = min(c for _, c in exact2)
    norm = {(r - r0, c - c0) for r, c in exact2}
    h = 1 + max(r for r, _ in norm)
    w = 1 + max(c for _, c in norm)
    return [[8 if (r, c) in norm else 0 for c in range(w)] for r in range(h)]


def main():
    gen, source, source_sha = load_selected_generator(TASK_ID, root=ROOT)
    expected_sha = "cc2688b4eedf869760ef88956f0fc170a606768d4753b57dc24800d28cdab4e5"
    assert source_sha == expected_sha

    sampled = []
    outside_counts = 0
    rival_agreements = 0
    for difficulty in (None, "easy", "medium", "hard"):
        for index in range(100):
            grid = gen.generate(700_000 + index, index, difficulty=difficulty)
            colors = sorted({v for row in grid for v in row})
            extra = [v for v in colors if v not in (0, 1, 2, 3)]
            outside_counts += bool(extra)
            intended = exact2_output(grid, (1, 2, 3))
            rival = exact2_output(grid, [v for v in colors if v != 0])
            rival_agreements += intended == rival
            sampled.append({
                "difficulty": difficulty,
                "sample_index": index,
                "colors": colors,
                "extra_nonzero_colors": extra,
                "self_check": gen.self_check(grid),
            })

    mismatch = None
    canonical = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    for row in canonical:
        grid = normalize_grid(row["input"])
        colors = sorted({v for line in grid for v in line if v != 0})
        rival = exact2_output(grid, colors)
        if rival != row["output"]:
            mismatch = {
                "variant": row["variant"],
                "split": row["split"],
                "pair_index": row["pair_index"],
                "input": grid,
                "canonical_output": row["output"],
                "all_nonzero_exact2_rival_output": rival,
                "nonzero_colors": colors,
                "ignored_by_canonical_rule": [v for v in colors if v not in (1, 2, 3)],
                "self_check": gen.self_check(grid),
            }
            break
    assert mismatch is not None

    (OUT / "input.json").write_text(json.dumps(mismatch["input"], indent=2) + "\n")
    (OUT / "rival.json").write_text(json.dumps(mismatch["all_nonzero_exact2_rival_output"], indent=2) + "\n")
    report = {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(source.relative_to(ROOT)),
        "generator_sha256": source_sha,
        "sample": {
            "draws": len(sampled),
            "bands": [None, "easy", "medium", "hard"],
            "seed_rule": "seed=700000+index, sample_index=index, 100 per band",
            "draws_with_nonzero_color_outside_1_2_3": outside_counts,
            "all_nonzero_exact2_rival_agreements": rival_agreements,
            "first_rows": sampled[:8],
        },
        "canonical_counterexample": mismatch,
        "finding": (
            "Every sampled generated grid omitted the canonical distractor color, so a rival that "
            "treats every nonzero color as a normalized shape is observationally identical on the "
            "sampled generator but changes a labeled canonical pair."
        ),
    }
    (OUT / "probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "generator_sha256": source_sha,
        "draws": len(sampled),
        "draws_with_extra": outside_counts,
        "rival_agreements": rival_agreements,
        "canonical_counterexample": {k: mismatch[k] for k in ("split", "pair_index", "nonzero_colors", "ignored_by_canonical_rule", "self_check")},
    }, indent=2))


if __name__ == "__main__":
    main()
