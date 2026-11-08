#!/usr/bin/env python3
"""Reproducible adversarial generator-domain census for the assigned audits."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import canonical_pairs  # noqa: E402

TARGETS = ("b4d9320e0d9d", "04204350555e")
BANDS = ("easy", "medium", "hard")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator(task_id: str):
    path = REPO / f"generators/{task_id}/generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module, path


def valid_diag_pairs(grid):
    rows = []
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            a, b = grid[r][c], grid[r][c + 1]
            d, e = grid[r + 1][c], grid[r + 1][c + 1]
            if a and a == e and b == 0 and d == 0:
                rows.append((r, c, a, "main"))
            if b and b == d and a == 0 and e == 0:
                rows.append((r, c, b, "anti"))
    return rows


def obstructed_diag_windows(grid):
    rows = []
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            a, b = grid[r][c], grid[r][c + 1]
            d, e = grid[r + 1][c], grid[r + 1][c + 1]
            if a and a == e and (b != 0 or d != 0):
                rows.append((r, c, a, "main"))
            if b and b == d and (a != 0 or e != 0):
                rows.append((r, c, b, "anti"))
    return rows


def permissive_square_rival(grid):
    """Wrong rival: fill each zero opposite corner even if the other is occupied."""
    src = deepcopy(grid)
    out = deepcopy(grid)
    for r in range(len(src) - 1):
        for c in range(len(src[0]) - 1):
            a, b = src[r][c], src[r][c + 1]
            d, e = src[r + 1][c], src[r + 1][c + 1]
            if a and a == e:
                if b == 0:
                    out[r][c + 1] = a
                if d == 0:
                    out[r + 1][c] = a
            if b and b == d:
                if a == 0:
                    out[r][c] = b
                if e == 0:
                    out[r + 1][c + 1] = b
    return out


def seeds(grid):
    return [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value]


def min_seed_distance(grid):
    pts = seeds(grid)
    if len(pts) < 2:
        return None
    return min(abs(r1-r2)+abs(c1-c2)
               for i, (r1,c1,_v1) in enumerate(pts)
               for r2,c2,_v2 in pts[i+1:])


def isolated_seed_rival(grid):
    """Wrong rival: expand only seeds with no other seed within distance two."""
    original = seeds(grid)
    out = deepcopy(grid)
    for r0, c0, color in original:
        if any(abs(r0-r1)+abs(c0-c1) <= 2
               for r1,c1,_ in original if (r1,c1) != (r0,c0)):
            continue
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                if abs(r-r0)+abs(c-c0) <= 2:
                    out[r][c] = color
    return out


def run_b4d(count: int):
    task = TARGETS[0]
    module, path = load_generator(task)
    pairs = canonical_pairs(task, root=REPO)
    stats = Counter()
    pair_counts = set()
    for index in range(count):
        band = BANDS[index % len(BANDS)]
        grid = module.generate(720000 + index, index, difficulty=band)
        stats["draws"] += 1
        stats["validator_rejections"] += bool(module.self_check(grid, difficulty=band))
        stats["draws_with_obstructed_diagonal"] += bool(obstructed_diag_windows(grid))
        pair_counts.add(len(valid_diag_pairs(grid)))
    override = {}
    for value in (1, 8):
        grid = module.generate(880001, 0, difficulty="medium", n_pairs=value)
        override[str(value)] = {
            "valid_pair_windows": len(valid_diag_pairs(grid)),
            "grid_sha256": hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest(),
        }
    return {
        "task_id": task,
        "generator_sha256": sha(path),
        "sample_protocol": {
            "draws": count,
            "seed_formula": "720000 + index",
            "sample_index_formula": "index",
            "difficulty_formula": "(easy,medium,hard)[index % 3]",
        },
        "canonical_pairs": len(pairs),
        "rival_canonical_mismatches": sum(permissive_square_rival(p["input"]) != p["output"] for p in pairs),
        **stats,
        "valid_pair_count_support": sorted(pair_counts),
        "n_pairs_override_probe": override,
        "n_pairs_override_outputs_identical": override["1"]["grid_sha256"] == override["8"]["grid_sha256"],
    }


def run_042(count: int):
    task = TARGETS[1]
    module, path = load_generator(task)
    pairs = canonical_pairs(task, root=REPO)
    stats = Counter()
    distances = set()
    for index in range(count):
        band = BANDS[index % len(BANDS)]
        grid = module.generate(730000 + index, index, difficulty=band)
        stats["draws"] += 1
        stats["validator_rejections"] += bool(module.self_check(grid, difficulty=band))
        distance = min_seed_distance(grid)
        if distance is not None:
            distances.add(distance)
            stats["multi_seed_draws"] += 1
            stats["draws_with_distance_le_2"] += distance <= 2
    return {
        "task_id": task,
        "generator_sha256": sha(path),
        "sample_protocol": {
            "draws": count,
            "seed_formula": "730000 + index",
            "sample_index_formula": "index",
            "difficulty_formula": "(easy,medium,hard)[index % 3]",
        },
        "canonical_pairs": len(pairs),
        "rival_canonical_mismatches": sum(isolated_seed_rival(p["input"]) != p["output"] for p in pairs),
        **stats,
        "minimum_seed_distance_support": sorted(distances),
    }


def main() -> int:
    report = {
        "schema": "assigned-audit-domain-probe-v1",
        "count_per_target": 1000,
        "targets": {
            TARGETS[0]: run_b4d(1000),
            TARGETS[1]: run_042(1000),
        },
        "probe_sha256": None,
    }
    report["probe_sha256"] = sha(Path(__file__))
    out = Path(__file__).with_name("census.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return int(any(row["rival_canonical_mismatches"] for row in report["targets"].values()))


if __name__ == "__main__":
    raise SystemExit(main())
