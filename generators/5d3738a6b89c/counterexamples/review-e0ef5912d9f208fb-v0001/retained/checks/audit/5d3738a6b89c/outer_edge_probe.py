#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "5d3738a6b89c"
REPO = Path.cwd()


def load_reference_probe():
    path = REPO / "generators" / TASK_ID / "workspace" / "reference_probe.py"
    spec = importlib.util.spec_from_file_location("audit_reference_probe", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def outer_border_ignored(grid, ref):
    """Plausible shortcut: never expand anchors on the outer grid border."""
    info = ref.parse(grid)
    lookup = {p["key"]: p["offsets"] for p in info["prototypes"]}
    output = copy.deepcopy(grid)
    for row in range(info["sep"] + 1, info["height"]):
        for col in range(info["width"]):
            key = grid[row][col]
            if key not in lookup:
                continue
            if row == info["height"] - 1 or col in (0, info["width"] - 1):
                continue
            for dr, dc in lookup[key]:
                rr, cc = row + dr, col + dc
                if rr >= info["sep"] + 1 and 0 <= rr < info["height"] and 0 <= cc < info["width"]:
                    output[rr][cc] = key
    return output


def witness_grid():
    grid = [[0] * 7 for _ in range(11)]
    # Prototype 2: horizontal three-cell mask; prototype 4: vertical three-cell mask.
    grid[1][0:3] = [2, 2, 2]
    for r in range(3):
        grid[r][3] = 9
        grid[r][5] = 4
    grid[3] = [9] * 7
    # One anchor per key, matching canonical anchor multiplicity.  The 2-anchor
    # sits on the left border, so its left mask cell clips while its right cell paints.
    grid[5][0] = 2
    grid[8][5] = 4
    return grid


def main():
    root = find_root(REPO)
    gen, source, source_hash = load_selected_generator(TASK_ID, root=root)
    ref = load_reference_probe()
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)

    canonical_failures = [
        i for i, pair in enumerate(canonical)
        if outer_border_ignored(pair["input"], ref) != pair["output"]
    ]
    generated_failures = []
    outer_anchor_draws = 0
    sampled = 0
    for band in ("easy", "medium", "hard"):
        for index in range(200):
            grid = gen.generate(50000 + index, index * 7 + 1, difficulty=band)
            sampled += 1
            info = ref.parse(grid)
            outer_anchor_draws += any(
                row == info["height"] - 1 or col in (0, info["width"] - 1)
                for anchors in info["anchors"].values()
                for row, col in anchors
            )
            expected = ref.reference_output(grid)
            if outer_border_ignored(grid, ref) != expected:
                generated_failures.append({"band": band, "index": index})

    witness = witness_grid()
    report = {
        "schema": "arcpuzzles-audit-outer-edge-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": source_hash,
        "generator_path": str(source.relative_to(root)),
        "rule_hash": gen.RULE_HASH,
        "canonical_pairs": len(canonical),
        "canonical_rival_failures": canonical_failures,
        "generated_samples": sampled,
        "generated_rival_failures": generated_failures,
        "generated_outer_border_anchor_draws": outer_anchor_draws,
        "witness_self_check": gen.self_check(witness),
        "witness_strict_check": gen.strict_canonical_like(witness),
        "witness_input": witness,
        "witness_python_intended": ref.reference_output(witness),
        "witness_rival_output": outer_border_ignored(witness, ref),
    }
    out_dir = REPO.parent / "checks" / "audit" / TASK_ID
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "input.json").write_text(json.dumps(witness, indent=2) + "\n")
    (out_dir / "rival.json").write_text(json.dumps(report["witness_rival_output"], indent=2) + "\n")
    (out_dir / "probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "canonical_rival_failures": len(canonical_failures),
        "generated_rival_failures": len(generated_failures),
        "generated_outer_border_anchor_draws": outer_anchor_draws,
        "sampled": sampled,
        "witness_valid": not report["witness_self_check"],
        "witness_disagrees": report["witness_python_intended"] != report["witness_rival_output"],
        "generator_sha256": source_hash,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
