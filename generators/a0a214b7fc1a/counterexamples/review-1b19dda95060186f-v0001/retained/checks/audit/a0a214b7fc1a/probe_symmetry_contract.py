#!/usr/bin/env python3
"""Find an advertised, self_check-accepted input with invisible rotations."""
from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "a0a214b7fc1a"
ASSIGNED_SHA256 = "6562b4433af7cfcb8dd01035103e2c22f50d95a1d445588f2b7057de8fcfb39c"


def rotate90(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def main() -> int:
    root = Path(find_root(__file__))
    gen, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    assert source_sha256 == ASSIGNED_SHA256, (source_sha256, ASSIGNED_SHA256)
    witness = None
    for seed in range(100):
        for sample_index in range(10):
            grid = gen.generate(
                seed,
                sample_index,
                difficulty="easy",
                grid_n=3,
                palette_size=2,
                texture="full_4fold_sym",
            )
            rotations = [grid]
            for _ in range(3):
                rotations.append(rotate90(rotations[-1]))
            if gen.self_check(grid) == [] and all(item == grid for item in rotations[1:]):
                witness = {
                    "seed": seed,
                    "sample_index": sample_index,
                    "difficulty": "easy",
                    "overrides": {
                        "grid_n": 3,
                        "palette_size": 2,
                        "texture": "full_4fold_sym",
                    },
                    "input": grid,
                    "self_check": [],
                    "is_4fold_symmetric": True,
                    "four_rotations": rotations,
                }
                break
        if witness is not None:
            break
    if witness is None:
        raise SystemExit("no accepted 4-fold-symmetric witness found")
    report = {
        "schema": "arcpuzzles-audit-symmetry-contract-v1",
        "task_id": TASK_ID,
        "generator_path": str(source_path.relative_to(root)),
        "generator_sha256": source_sha256,
        "declared_invariant": "grid is NOT 4-fold symmetric (so rotations differ)",
        "finding": (
            "The advertised full_4fold_sym override bypasses asymmetry repair and "
            "self_check does not enforce the declared non-symmetry invariant."
        ),
        **witness,
    }
    out = Path("../checks/audit/a0a214b7fc1a/symmetry-contract.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    Path("../checks/audit/a0a214b7fc1a/input.json").write_text(
        json.dumps(witness["input"], indent=2) + "\n"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
