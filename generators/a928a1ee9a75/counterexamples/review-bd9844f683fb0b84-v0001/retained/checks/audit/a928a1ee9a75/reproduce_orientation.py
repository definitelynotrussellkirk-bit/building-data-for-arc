#!/usr/bin/env python3
"""Source-bound audit probe for a928a1ee9a75; does not modify the target."""
from __future__ import annotations

import hashlib
import importlib
import json
from collections import Counter, defaultdict
from pathlib import Path

WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
TASK = "a928a1ee9a75"
GEN_PATH = REPO / "generators" / TASK / "generator.py"
CANONICAL = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grid_sha(grid: list[list[int]]) -> str:
    return sha256_bytes(json.dumps(grid, separators=(",", ":")).encode())


def pair_groups(grid):
    by_color = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                by_color[value].append((r, c))
    return [cells for _, cells in sorted(by_color.items()) if len(cells) == 2]


def pair_orientation(cells):
    if cells[0][0] == cells[1][0]:
        return "horizontal"
    if cells[0][1] == cells[1][1]:
        return "vertical"
    return "diagonal"


def canonical_band(grid):
    pairs = pair_groups(grid)
    if len(pairs) != 2:
        raise ValueError(f"expected two pairs, got {len(pairs)}")
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    ori = pair_orientation(pairs[0])
    if ori == "horizontal":
        top = min(pairs[0][0][0], pairs[1][0][0])
        bottom = max(pairs[0][0][0], pairs[1][0][0])
        c0, c1 = sorted(c for _, c in pairs[0])
        for r in range(top, bottom + 1):
            for c in range(c0, c1 + 1):
                out[r][c] = 8
    elif ori == "vertical":
        left = min(pairs[0][0][1], pairs[1][0][1])
        right = max(pairs[0][0][1], pairs[1][0][1])
        r0, r1 = sorted(r for r, _ in pairs[0])
        for r in range(r0, r1 + 1):
            for c in range(left, right + 1):
                out[r][c] = 8
    else:
        raise ValueError("diagonal pair")
    return out


def horizontal_only_rival(grid):
    pairs = pair_groups(grid)
    h, w = len(grid), len(grid[0])
    if len(pairs) != 2 or pair_orientation(pairs[0]) != "horizontal":
        return [[0] * w for _ in range(h)]
    return canonical_band(grid)


def load_task():
    for line in CANONICAL.read_text().splitlines():
        obj = json.loads(line)
        if obj.get("task_id") == TASK:
            return obj
    raise RuntimeError("canonical task not found")


def main():
    gen = importlib.import_module(f"generators.{TASK}.generator")
    counts = Counter()
    unique = set()
    self_check_failures = []
    rival_mismatches = []
    sample_count = 0
    for band in ("easy", "medium", "hard"):
        for sample_index in range(200):
            grid = gen.generate(211, sample_index, difficulty=band)
            sample_count += 1
            orientations = tuple(sorted(pair_orientation(p) for p in pair_groups(grid)))
            counts[(band, orientations)] += 1
            unique.add(grid_sha(grid))
            errors = gen.self_check(grid, difficulty=band)
            if errors:
                self_check_failures.append({"band": band, "sample_index": sample_index, "errors": errors})
            expected = canonical_band(grid)
            rival = horizontal_only_rival(grid)
            if rival != expected:
                rival_mismatches.append({"band": band, "sample_index": sample_index})

    task = load_task()
    vertical_witness = None
    for split, examples in (("train", task.get("train", [])), ("test", [task.get("test")])):
        for index, example in enumerate(e for e in examples if e):
            orientations = [pair_orientation(p) for p in pair_groups(example["input"])]
            if orientations and all(o == "vertical" for o in orientations):
                expected = example["output"]
                reference = canonical_band(example["input"])
                rival = horizontal_only_rival(example["input"])
                vertical_witness = {
                    "split": split,
                    "index": index,
                    "orientations": orientations,
                    "input": example["input"],
                    "canonical_output": expected,
                    "reference_matches_canonical": reference == expected,
                    "horizontal_only_output": rival,
                    "horizontal_only_matches_canonical": rival == expected,
                    "canonical_nonzero_count": sum(v != 0 for row in expected for v in row),
                    "rival_nonzero_count": sum(v != 0 for row in rival for v in row),
                }
                break
        if vertical_witness:
            break

    report = {
        "schema": "arc-review-audit-orientation-v1",
        "task_id": TASK,
        "generator_sha256": sha256_bytes(GEN_PATH.read_bytes()),
        "canonical_ledger_sha256": sha256_bytes(CANONICAL.read_bytes()),
        "probe": {"seed": 211, "per_band": 200, "total": sample_count},
        "orientation_counts": [
            {"band": band, "pair_orientations": list(orientations), "count": count}
            for (band, orientations), count in sorted(counts.items())
        ],
        "unique_input_count": len(unique),
        "self_check_failure_count": len(self_check_failures),
        "self_check_failures": self_check_failures[:10],
        "horizontal_only_rival_generated_mismatch_count": len(rival_mismatches),
        "horizontal_only_rival_generated_mismatches": rival_mismatches[:10],
        "canonical_vertical_witness": vertical_witness,
        "conclusion": (
            "The source-bound sampler emitted only horizontal pair orientations, so a horizontal-only "
            "rival matched all 600 generated cases. The canonical ledger contains a vertical witness "
            "on which that rival fails."
        ),
    }
    out = Path(__file__).with_name("orientation_witness.json")
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "out": str(out),
        "generator_sha256": report["generator_sha256"],
        "total": sample_count,
        "unique": len(unique),
        "orientation_counts": report["orientation_counts"],
        "self_check_failures": len(self_check_failures),
        "rival_generated_mismatches": len(rival_mismatches),
        "vertical_witness_found": vertical_witness is not None,
        "vertical_rival_matches": None if not vertical_witness else vertical_witness["horizontal_only_matches_canonical"],
    }, indent=2))


if __name__ == "__main__":
    main()
