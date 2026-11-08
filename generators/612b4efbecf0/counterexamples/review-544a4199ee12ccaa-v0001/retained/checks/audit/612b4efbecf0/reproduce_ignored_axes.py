#!/usr/bin/env python3
"""Reproduce advertised override axes that do not change 612b4efbecf0."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "612b4efbecf0"


def digest(value) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(body).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    root = find_root(__file__)
    generator, source, source_sha = load_selected_generator(TASK_ID, root=root)
    seed = 314159
    sample_index = 7
    difficulty = "medium"

    pairs = [
        (
            "shape_pair_kind",
            {"shape_pair_kind": "dense_vs_sparse"},
            {"shape_pair_kind": "L_vs_T"},
        ),
        ("anchor_corner", {"anchor_corner": False}, {"anchor_corner": True}),
        (
            "asymmetry_force",
            {"asymmetry_force": False},
            {"asymmetry_force": True},
        ),
    ]
    checks = []
    for axis, left_request, right_request in pairs:
        left = generator.generate(
            seed, sample_index, difficulty=difficulty, **left_request
        )
        right = generator.generate(
            seed, sample_index, difficulty=difficulty, **right_request
        )
        checks.append(
            {
                "axis": axis,
                "left_request": left_request,
                "right_request": right_request,
                "left_grid": left,
                "right_grid": right,
                "left_sha256": digest(left),
                "right_sha256": digest(right),
                "identical": left == right,
                "left_self_check": generator.self_check(left),
                "right_self_check": generator.self_check(right),
            }
        )

    report = {
        "schema": "audit-612b4efbecf0-ignored-axes-v1",
        "task_id": TASK_ID,
        "generator_path": str(source.relative_to(root)),
        "generator_sha256": source_sha,
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "checks": checks,
        "all_advertised_axes_ignored": all(row["identical"] for row in checks),
        "finding": (
            "shape_pair_kind, anchor_corner, and asymmetry_force are advertised "
            "as controls, but changing each one in isolation leaves the exact "
            "generated grid unchanged."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"out": str(args.out), "all_ignored": report["all_advertised_axes_ignored"]}))
    return int(not report["all_advertised_axes_ignored"])


if __name__ == "__main__":
    raise SystemExit(main())
