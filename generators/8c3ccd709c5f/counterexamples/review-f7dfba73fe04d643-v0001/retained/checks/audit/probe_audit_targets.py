#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

PACKET = Path(__file__).resolve().parents[2]
REPO = PACKET / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def marker_vector(grid):
    one = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1)
    two = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2)
    return two[0] - one[0], two[1] - one[1]


def main():
    first, first_path = load("8c3ccd709c5f")
    blank = [[0] * 12 for _ in range(12)]
    requested = {"grid_h": 22, "grid_w": 24, "orientation": "h", "n_decoys": 3}
    generated = first.generate(2026, 7, difficulty="easy", **requested)
    unknown_accepted = True
    unknown_error = None
    try:
        first.generate(2026, 7, difficulty="easy", __unknown_axis__=1)
    except Exception as exc:  # evidence records whether the typo is rejected
        unknown_accepted = False
        unknown_error = f"{type(exc).__name__}: {exc}"

    second, second_path = load("7b0c20fe6f33")
    threes = Counter()
    vectors = Counter()
    for difficulty in ("easy", "medium", "hard"):
        for index in range(100):
            grid = second.generate(50_000 + index, index, difficulty=difficulty)
            threes[(difficulty, sum(value == 3 for row in grid for value in row))] += 1
            vectors[(difficulty, marker_vector(grid))] += 1
    v0 = second.generate(1234, 56, difficulty="medium", vector_choice=0)
    v3 = second.generate(1234, 56, difficulty="medium", vector_choice=3)
    second_unknown_accepted = True
    second_unknown_error = None
    try:
        second.generate(1234, 56, __unknown_axis__=1)
    except Exception as exc:
        second_unknown_accepted = False
        second_unknown_error = f"{type(exc).__name__}: {exc}"

    report = {
        "schema": "arcpuzzles-adversarial-audit-probe-v1",
        "8c3ccd709c5f": {
            "generator_sha256": sha256(first_path),
            "blank_grid_self_check_errors": first.self_check(blank),
            "blank_grid_accepted": first.self_check(blank) == [],
            "requested_overrides": requested,
            "observed_dimensions": [len(generated), len(generated[0])],
            "dimensions_honored": [len(generated), len(generated[0])] == [22, 24],
            "unknown_override_accepted": unknown_accepted,
            "unknown_override_error": unknown_error,
        },
        "7b0c20fe6f33": {
            "generator_sha256": sha256(second_path),
            "draws_per_band": 100,
            "color3_count_histogram": {
                f"{difficulty}:{count}": frequency
                for (difficulty, count), frequency in sorted(threes.items())
            },
            "marker_vector_histogram": {
                f"{difficulty}:{dr},{dc}": frequency
                for (difficulty, (dr, dc)), frequency in sorted(vectors.items())
            },
            "vector_choice_0_equals_3_same_seed": v0 == v3,
            "vector_choice_0_observed": list(marker_vector(v0)),
            "vector_choice_3_observed": list(marker_vector(v3)),
            "unknown_override_accepted": second_unknown_accepted,
            "unknown_override_error": second_unknown_error,
        },
    }
    out = Path(__file__).with_name("audit_probe.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
