#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "506b65933421"
OUT = Path(__file__).resolve().parent


def colors(grid):
    return tuple(sorted({v for row in grid for v in row if v != 0}))


def first_color_only_bbox(grid):
    h, w = len(grid), len(grid[0])
    first = next(v for row in grid for v in row if v != 0)
    cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == first]
    r1, r2 = min(r for r, _ in cells), max(r for r, _ in cells)
    c1, c2 = min(c for _, c in cells), max(c for _, c in cells)
    out = [[0] * w for _ in range(h)]
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            out[r][c] = first
    return out


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def main():
    root = find_root(__file__)
    module, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    seed = 90210
    histogram = Counter()
    self_check_failures = []
    for band in ("easy", "medium", "hard"):
        for sample_index in range(100):
            grid = module.generate(seed, sample_index, difficulty=band)
            histogram[len(colors(grid))] += 1
            errors = module.self_check(grid)
            if errors:
                self_check_failures.append(
                    {"difficulty": band, "sample_index": sample_index, "errors": errors}
                )

    override_histogram = Counter()
    for sample_index in range(20):
        grid = module.generate(seed, sample_index, num_colors=2)
        override_histogram[len(colors(grid))] += 1

    pair = canonical_pairs(TASK_ID, root=root, labeled_only=True)[0]
    grid = pair["input"]
    expected = pair["output"]
    rival = first_color_only_bbox(grid)
    evidence = {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(source_path),
        "generator_sha256": source_sha256,
        "version": module.VERSION,
        "seed": seed,
        "normal_samples": {
            "count": 300,
            "bands": {"easy": 100, "medium": 100, "hard": 100},
            "distinct_color_count_histogram": dict(sorted(histogram.items())),
            "self_check_failures": self_check_failures,
        },
        "num_colors_2_override": {
            "count": 20,
            "distinct_color_count_histogram": dict(sorted(override_histogram.items())),
        },
        "canonical_counterexample": {
            "source": "canonical labeled pair 0",
            "nonzero_colors": list(colors(grid)),
            "passes_self_check": module.self_check(grid) == [],
            "expected_output_sha256": digest(expected),
            "first_color_only_output_sha256": digest(rival),
            "outputs_differ": expected != rival,
        },
        "interpretation": (
            "All measured generated inputs contain one nonzero color and the "
            "advertised num_colors=2 override remains unobservable. A solver "
            "that processes only the first color fits generated data but fails "
            "the lawful two-color canonical pair."
        ),
    }
    (OUT / "input.json").write_text(json.dumps({"input": grid}, indent=2) + "\n")
    (OUT / "canonical-expected.json").write_text(json.dumps(expected, indent=2) + "\n")
    (OUT / "rival.json").write_text(json.dumps(rival, indent=2) + "\n")
    (OUT / "probe.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "generator_sha256": source_sha256,
        "normal_histogram": dict(histogram),
        "override_histogram": dict(override_histogram),
        "canonical_outputs_differ": expected != rival,
    }, sort_keys=True))
    if histogram != Counter({1: 300}):
        raise SystemExit("normal generator no longer reproduces one-color shortcut")
    if override_histogram != Counter({1: 20}):
        raise SystemExit("num_colors=2 override no longer reproduces shortcut")
    if expected == rival:
        raise SystemExit("canonical counterexample no longer distinguishes rival")


if __name__ == "__main__":
    main()
