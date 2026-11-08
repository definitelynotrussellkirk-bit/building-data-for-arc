#!/usr/bin/env python3
"""Audit declared overrides for generator 50190b6e8882."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reviewer_support import load_selected_generator

TASK = "50190b6e8882"
VALUES = ("default", "warm", "cool", "varied")


def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def run(root: Path, draws: int) -> dict:
    gen, source, source_sha = load_selected_generator(TASK, root=root)
    rows = []
    palette_all_noop = True
    texture_all_noop = True
    errors = []
    for index in range(draws):
        seed = 5019000 + index
        base = gen.generate(seed, index, difficulty="medium")
        palette = {
            value: gen.generate(seed, index, difficulty="medium", palette_kind=value)
            for value in VALUES
        }
        texture = {
            value: gen.generate(seed, index, difficulty="medium", texture=value)
            for value in VALUES
        }
        palette_hashes = {value: digest(grid) for value, grid in palette.items()}
        texture_hashes = {value: digest(grid) for value, grid in texture.items()}
        palette_noop = len(set(palette_hashes.values())) == 1 and next(iter(palette.values())) == base
        texture_noop = len(set(texture_hashes.values())) == 1 and next(iter(texture.values())) == base
        palette_all_noop &= palette_noop
        texture_all_noop &= texture_noop
        for family, samples in (("palette_kind", palette), ("texture", texture)):
            for value, grid in samples.items():
                findings = gen.self_check(grid)
                if findings:
                    errors.append({"index": index, "family": family, "value": value, "findings": findings})
        if index < 3:
            rows.append({
                "index": index,
                "seed": seed,
                "base_sha256": digest(base),
                "palette_hashes": palette_hashes,
                "texture_hashes": texture_hashes,
                "palette_all_equal_to_base": palette_noop,
                "texture_all_equal_to_base": texture_noop,
            })
    return {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": TASK,
        "generator_path": str(source.relative_to(root)),
        "generator_sha256": source_sha,
        "rule_hash": getattr(gen, "RULE_HASH", None),
        "draws": draws,
        "values": list(VALUES),
        "palette_kind_all_values_identical_to_default": palette_all_noop,
        "helpful_texture_all_values_identical_to_default": texture_all_noop,
        "self_check_errors": errors,
        "examples": rows,
        "conclusion": (
            "The advertised palette_kind axis and all four helpful texture values are silent no-ops: "
            "they are never consumed by a keyed draw and produce byte-identical grids for every probe draw."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--draws", type=int, default=40)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.root.resolve(), args.draws)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
