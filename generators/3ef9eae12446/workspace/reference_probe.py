"""Independent review oracle and curriculum probe for task 3ef9eae12446.

This module deliberately does not import the generator's semantic helpers.  It
is test/review tooling, not a replacement for the canonical Racket authority.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

TASK = "3ef9eae12446"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path: str | Path | None = None):
    target = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_3ef9eae12446", target)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {target}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    from reviewer_support import canonical_pairs as read_pairs, find_root

    return read_pairs(TASK, root=find_root(__file__))


def _rectangular(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected nonempty rows")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("ragged grid")
    return len(grid), width


def ring_centers(grid: Any) -> dict[tuple[int, int], int]:
    """Return centers satisfying the literal eight-cell uniform-border rule."""
    height, width = _rectangular(grid)
    result: dict[tuple[int, int], int] = {}
    for row0 in range(height - 2):
        for col0 in range(width - 2):
            border = [
                grid[row0 + dr][col0 + dc]
                for dr, dc in (
                    (0, 0), (0, 1), (0, 2),
                    (1, 0),         (1, 2),
                    (2, 0), (2, 1), (2, 2),
                )
            ]
            color = border[0]
            if color != 0 and grid[row0 + 1][col0 + 1] == 0 and all(v == color for v in border):
                result[(row0 + 1, col0 + 1)] = color
    return result


def intended_output(grid: Any) -> list[list[int]]:
    """Independent Python rendering of the written rule, from original pixels."""
    _rectangular(grid)
    out = [list(row) for row in grid]
    for (row, col), color in ring_centers(grid).items():
        out[row][col] = color
    return out


def orthogonal_neighbors_only(grid: Any) -> list[list[int]]:
    """Plausible shortcut: ignore corners and check only N/S/E/W."""
    height, width = _rectangular(grid)
    out = [list(row) for row in grid]
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            arms = (
                grid[row - 1][col], grid[row + 1][col],
                grid[row][col - 1], grid[row][col + 1],
            )
            if grid[row][col] == 0 and arms[0] != 0 and len(set(arms)) == 1:
                out[row][col] = arms[0]
    return out


def motif_features(grid: Any) -> dict[str, Any]:
    """Classify explicit 3x3 target/decoy windows without generator code."""
    height, width = _rectangular(grid)
    targets = ring_centers(grid)
    crosses: set[tuple[int, int]] = set()
    mixed: set[tuple[int, int]] = set()
    occupied: set[tuple[int, int]] = set()
    for row0 in range(height - 2):
        for col0 in range(width - 2):
            center = (row0 + 1, col0 + 1)
            border = [
                grid[row0 + dr][col0 + dc]
                for dr, dc in (
                    (0, 0), (0, 1), (0, 2),
                    (1, 0),         (1, 2),
                    (2, 0), (2, 1), (2, 2),
                )
            ]
            center_value = grid[center[0]][center[1]]
            arms = (
                grid[row0][col0 + 1], grid[row0 + 2][col0 + 1],
                grid[row0 + 1][col0], grid[row0 + 1][col0 + 2],
            )
            corners = (
                grid[row0][col0], grid[row0][col0 + 2],
                grid[row0 + 2][col0], grid[row0 + 2][col0 + 2],
            )
            if center_value == 0 and arms[0] != 0 and len(set(arms)) == 1 and all(v == 0 for v in corners):
                crosses.add(center)
            nonzero = [v for v in border if v != 0]
            if center_value == 0 and len(nonzero) == 8 and len(set(border)) > 1:
                mixed.add(center)
            if center_value != 0 and border[0] != 0 and len(set(border)) == 1 and center_value != border[0]:
                occupied.add(center)
    return {
        "targets": targets,
        "crosses": crosses,
        "mixed": mixed,
        "occupied": occupied,
    }


def observed_profile(grid: Any) -> str:
    features = motif_features(grid)
    n_targets = len(features["targets"])
    if n_targets == 2 and not (features["crosses"] or features["mixed"] or features["occupied"]):
        return "multi_target"
    if n_targets != 1:
        raise ValueError(f"expected one or two target rings, found {n_targets}")
    signatures = {
        "cross_guard": bool(features["crosses"]),
        "mixed_guard": bool(features["mixed"]),
        "filled_guard": bool(features["occupied"]),
    }
    hits = [name for name, present in signatures.items() if present]
    if len(hits) != 1:
        raise ValueError(f"ambiguous profile signatures: {hits}")
    return hits[0]


def witness_input() -> list[list[int]]:
    """Exact counterexample: one ring plus a cornerless cross."""
    return [
        [2, 2, 2, 0, 3, 0],
        [2, 0, 2, 3, 0, 3],
        [2, 2, 2, 0, 3, 0],
        [0, 0, 0, 0, 0, 0],
    ]


def audit(module, per_band: int = 100) -> dict[str, Any]:
    """Reproducible, source-bound sampling report for future reviewers."""
    source_path = Path(module.__file__).resolve()
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    by_band: dict[str, Any] = {}
    all_inputs: set[str] = set()
    for band in (None, "easy", "medium", "hard"):
        counts = Counter()
        shapes: set[tuple[int, int]] = set()
        profiles: set[str] = set()
        inputs: set[str] = set()
        for index in range(per_band):
            seed = 7001 + index
            grid = module.generate(seed, index, difficulty=band)
            encoded = json.dumps(grid, separators=(",", ":"), sort_keys=False)
            digest = hashlib.sha256(encoded.encode()).hexdigest()
            inputs.add(digest)
            all_inputs.add(digest)
            shapes.add((len(grid), len(grid[0])))
            profile = observed_profile(grid)
            profiles.add(profile)
            counts[f"profile:{profile}"] += 1
            counts["self_check_rejections"] += bool(module.self_check(grid))
            counts["nondeterministic"] += grid != module.generate(seed, index, difficulty=band)
            counts["oracle_changed"] += intended_output(grid) != grid
            counts["orthogonal_disagreement"] += intended_output(grid) != orthogonal_neighbors_only(grid)
        by_band[str(band)] = {
            "counts": dict(counts),
            "distinct_inputs": len(inputs),
            "shapes": sorted([list(shape) for shape in shapes]),
            "profiles": sorted(profiles),
        }
    witness = witness_input()
    return {
        "schema": "3ef9eae12446-independent-audit-v1",
        "generator_sha256": source_hash,
        "per_band": per_band,
        "sample_schedule": "seed=7001+i, sample_index=i, crossed with None/easy/medium/hard",
        "distinct_inputs_union": len(all_inputs),
        "canonical_pairs": len(canonical_pairs()),
        "canonical_intended_matches": all(intended_output(pair["input"]) == pair["output"] for pair in canonical_pairs()),
        "canonical_orthogonal_shortcut_matches": all(orthogonal_neighbors_only(pair["input"]) == pair["output"] for pair in canonical_pairs()),
        "by_band": by_band,
        "witness": {
            "input": witness,
            "intended_python": intended_output(witness),
            "orthogonal_neighbors_only": orthogonal_neighbors_only(witness),
        },
        "warning": "Finite generated samples and one declared rival do not prove universal identifiability.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator")
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--out")
    args = parser.parse_args()
    report = audit(load_generator(args.generator), args.per_band)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
