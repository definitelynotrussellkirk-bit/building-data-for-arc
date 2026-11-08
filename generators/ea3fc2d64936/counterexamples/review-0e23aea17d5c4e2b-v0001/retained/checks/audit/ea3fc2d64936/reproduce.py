from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root

TASK_ID = "ea3fc2d64936"
HERE = Path(__file__).resolve().parent
ROOT = find_root(Path(__file__).resolve().parents[3] / "repo")
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GENERATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 0 or (sr, sc) in seen:
                continue
            color = grid[sr][sc]
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append(cells)
    return out


def normalize(cells):
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return {(r - min_r, c - min_c) for r, c in cells}


def overlay(grid, *, force_origin: bool):
    masks = [normalize(cells) for cells in components(grid)]
    if force_origin:
        masks = [mask | {(0, 0)} for mask in masks]
    h = max(r for mask in masks for r, _ in mask) + 1
    w = max(c for mask in masks for _, c in mask) + 1
    palette = {0: 0, 1: 2, 2: 3, 3: 4}
    return [
        [palette.get(sum((r, c) in mask for mask in masks), 6) for c in range(w)]
        for r in range(h)
    ]


def main() -> None:
    generator = load_generator()
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    canonical_rows = []
    for pair in pairs:
        grid = pair["input"]
        errors = generator.self_check(grid)
        masks = [normalize(cells) for cells in components(grid)]
        canonical_rows.append(
            {
                "pair_index": pair["pair_index"],
                "split": pair["split"],
                "validator_errors": errors,
                "all_masks_contain_normalized_origin": all((0, 0) in m for m in masks),
            }
        )

    total = 0
    origin_forced = 0
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(50):
            for sample_index in range(3):
                grid = generator.generate(seed, sample_index, difficulty=difficulty)
                total += 1
                masks = [normalize(cells) for cells in components(grid)]
                origin_forced += int(all((0, 0) in m for m in masks))

    chosen = pairs[0]
    intended = overlay(chosen["input"], force_origin=False)
    rival = overlay(chosen["input"], force_origin=True)
    assert intended == chosen["output"]
    assert rival != intended
    (HERE / "input.json").write_text(json.dumps(chosen["input"], indent=2) + "\n")
    (HERE / "canonical_output.json").write_text(json.dumps(chosen["output"], indent=2) + "\n")
    (HERE / "forced_origin_rival.json").write_text(json.dumps(rival, indent=2) + "\n")

    report = {
        "schema": "arcpuzzles-audit-reproduction-v1",
        "task_id": TASK_ID,
        "classification": "confirmed_unresolved_distribution_and_validator_defect",
        "generator_path": str(GENERATOR_PATH.relative_to(ROOT)),
        "generator_sha256": sha256_file(GENERATOR_PATH),
        "command": "PYTHONPATH=src:shared/runtime python3 ../checks/audit/ea3fc2d64936/reproduce.py",
        "cwd": str(ROOT),
        "canonical_pairs_checked": len(canonical_rows),
        "canonical_pairs_rejected": sum(bool(row["validator_errors"]) for row in canonical_rows),
        "canonical_rows": canonical_rows,
        "generated_sample": {
            "difficulties": ["easy", "medium", "hard"],
            "seed_range": [0, 49],
            "sample_index_range": [0, 2],
            "total": total,
            "all_masks_contain_normalized_origin": origin_forced,
        },
        "counterexample": {
            "source": "canonical labeled pair 0",
            "passes_target_validator": not bool(generator.self_check(chosen["input"])),
            "target_validator_errors": generator.self_check(chosen["input"]),
            "canonical_output_matches_independent_overlay": True,
            "forced_origin_rival_differs": True,
            "different_cells": sum(
                intended[r][c] != rival[r][c]
                for r in range(len(intended))
                for c in range(len(intended[0]))
            ),
            "input_path": "checks/audit/ea3fc2d64936/input.json",
            "canonical_output_path": "checks/audit/ea3fc2d64936/canonical_output.json",
            "rival_output_path": "checks/audit/ea3fc2d64936/forced_origin_rival.json",
        },
        "target_edited": False,
    }
    (HERE / "summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
