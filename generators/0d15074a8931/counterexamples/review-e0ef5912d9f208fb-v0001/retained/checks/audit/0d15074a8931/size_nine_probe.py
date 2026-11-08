#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "0d15074a8931"
REPO = Path.cwd()


def capped_size_rival(gen, grid):
    """Plausible support shortcut: keep centers only for dimensions <= 7."""
    analysis = gen._analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    out = [[0] * analysis["width"] for _ in range(analysis["height"])]
    for obj in analysis["rects"]:
        if max(obj["height"], obj["width"]) > 7:
            continue
        r1, c1, r2, c2 = obj["bbox"]
        out[(r1 + r2) // 2][(c1 + c2) // 2] = obj["color"]
    return out


def witness_grid():
    grid = [[0] * 12 for _ in range(12)]
    for r in range(9):
        for c in range(3):
            grid[r][c] = 4
    for r in range(9, 12):
        for c in range(9, 12):
            grid[r][c] = 6
    return grid


def main():
    root = find_root(REPO)
    gen, source, source_hash = load_selected_generator(TASK_ID, root=root)
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    canonical_failures = [
        i for i, pair in enumerate(canonical)
        if capped_size_rival(gen, pair["input"]) != pair["output"]
    ]
    generated_failures = []
    max_seen = 0
    sampled = 0
    for band in ("easy", "medium", "hard"):
        for index in range(200):
            grid = gen.generate(70000 + index, index * 5 + 2, difficulty=band)
            sampled += 1
            analysis = gen._analyze(grid)
            max_seen = max(
                max_seen,
                *(max(obj["height"], obj["width"]) for obj in analysis["rects"]),
            )
            if capped_size_rival(gen, grid) != gen.rule_mirror(grid):
                generated_failures.append({"band": band, "index": index})

    witness = witness_grid()
    report = {
        "schema": "arcpuzzles-audit-size-nine-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": source_hash,
        "generator_path": str(source.relative_to(root)),
        "rule_hash": gen.RULE_HASH,
        "canonical_pairs": len(canonical),
        "canonical_rival_failures": canonical_failures,
        "generated_samples": sampled,
        "generated_rival_failures": generated_failures,
        "generated_max_rectangle_dimension": max_seen,
        "witness_self_check": gen.self_check(witness),
        "witness_strict_check": gen.strict_canonical_like(witness),
        "witness_input": witness,
        "witness_python_intended": gen.rule_mirror(witness),
        "witness_rival_output": capped_size_rival(gen, witness),
    }
    out_dir = REPO.parent / "checks" / "audit" / TASK_ID
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "input.json").write_text(json.dumps(witness, indent=2) + "\n")
    (out_dir / "rival.json").write_text(json.dumps(report["witness_rival_output"], indent=2) + "\n")
    (out_dir / "probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "canonical_rival_failures": len(canonical_failures),
        "generated_rival_failures": len(generated_failures),
        "generated_max_rectangle_dimension": max_seen,
        "sampled": sampled,
        "witness_valid": not report["witness_self_check"],
        "witness_disagrees": report["witness_python_intended"] != report["witness_rival_output"],
        "generator_sha256": source_hash,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
