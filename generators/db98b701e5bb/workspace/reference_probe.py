"""Independent oracle, contract observer, and qualification probe for db98b701e5bb.

This file is reviewer tooling, not label authority.  It deliberately does not
import semantic helpers from the generator under review, so task-local tests can
catch a generator-side implementation mistake instead of repeating it.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Callable

TASK_ID = "db98b701e5bb"
EXPECTED_RULE_HASH = "da19a5612a17"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))

PROFILE_BY_SIZES = {
    (3, 3, 5): "tie_small",
    (3, 4, 5): "three_distinct",
    (3, 9): "two_large",
    (1, 2, 3, 5): "four_varied",
}
CANONICAL_PROFILES = {(8, 10, 3), (8, 11, 3), (9, 12, 3), (10, 13, 3)}


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or ROOT / f"generators/{TASK_ID}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator_db98b701e5bb", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    from reviewer_support import canonical_pairs as portable_pairs, find_root
    return portable_pairs(TASK_ID, root=find_root(__file__))


def components4(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nxt = (cr + dr, cc + dc)
                    if (
                        0 <= nxt[0] < h
                        and 0 <= nxt[1] < w
                        and grid[nxt[0]][nxt[1]] == color
                        and nxt not in seen
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            result.append(sorted(cells))
    return result


def reference_output(grid: list[list[int]]) -> list[list[int]]:
    red = components4(grid, 2)
    if not red:
        raise ValueError("no color-2 component")
    max_size = max(map(len, red))
    largest = [component for component in red if len(component) == max_size]
    if len(largest) != 1:
        raise ValueError("largest color-2 component is not unique")
    out = deepcopy(grid)
    for r, c in largest[0]:
        out[r][c] = 8
    return out


def _ranked_red(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    return sorted(components4(grid, 2), key=lambda cells: min(cells))


def recolor_rank(grid: list[list[int]], rank: int) -> list[list[int]]:
    red = _ranked_red(grid)
    if not red:
        raise ValueError("no color-2 component")
    chosen = red[rank]
    out = deepcopy(grid)
    for r, c in chosen:
        out[r][c] = 8
    return out


def recolor_smallest(grid: list[list[int]]) -> list[list[int]]:
    red = _ranked_red(grid)
    chosen = min(red, key=lambda cells: (len(cells), min(cells)))
    out = deepcopy(grid)
    for r, c in chosen:
        out[r][c] = 8
    return out


def bbox_area(cells: list[tuple[int, int]]) -> int:
    rows = [r for r, _ in cells]
    columns = [c for _, c in cells]
    return (max(rows) - min(rows) + 1) * (max(columns) - min(columns) + 1)


def recolor_largest_bbox(grid: list[list[int]]) -> list[list[int]]:
    """Plausible shortcut: maximize bounding-box area, breaking ties by scan order."""
    red = _ranked_red(grid)
    chosen = max(red, key=bbox_area)
    out = deepcopy(grid)
    for r, c in chosen:
        out[r][c] = 8
    return out


def observed(grid: list[list[int]]) -> dict:
    red_sizes = tuple(sorted(len(component) for component in components4(grid, 2)))
    if red_sizes not in PROFILE_BY_SIZES:
        raise ValueError(f"unknown red component profile: {red_sizes}")
    other_colors = sorted({value for row in grid for value in row} - {0, 2, 8})
    if len(other_colors) != 1:
        raise ValueError(f"expected one distractor color, found {other_colors}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "component_profile": PROFILE_BY_SIZES[red_sizes],
        "distractor_color": other_colors[0],
    }


def largest_scan_rank(grid: list[list[int]]) -> int:
    red = _ranked_red(grid)
    largest = max(red, key=len)
    return red.index(largest)


def audit(module, count: int) -> dict:
    report: dict = {
        "schema": "db98b701e5bb-independent-audit-v1",
        "generator_version": getattr(module, "VERSION", None),
        "rule_hash": getattr(module, "RULE_HASH", None),
        "canonical": [],
        "bands": {},
    }
    for index, pair in enumerate(canonical_pairs()):
        report["canonical"].append(
            {
                "index": index,
                "split": pair.get("split"),
                "self_check": module.self_check(pair["input"]),
                "strict": module.strict_canonical_like(pair["input"])
                if hasattr(module, "strict_canonical_like")
                else ["missing strict_canonical_like"],
                "oracle_matches": reference_output(pair["input"]) == pair["output"],
            }
        )
    for band in ("easy", "medium", "hard"):
        profiles: set[tuple[int, int, int]] = set()
        profile_names: set[str] = set()
        ranks: set[int] = set()
        colors: set[int] = set()
        hashes: set[str] = set()
        failures: list[dict] = []
        exact_hits = 0
        rival_disagreements = {"first": 0, "last": 0, "smallest": 0, "largest_bbox_area": 0}
        for index in range(count):
            seed = 10_000 + index
            sample_index = index * 7 + 3
            grid = module.generate(seed, sample_index, difficulty=band)
            errors = module.self_check(grid)
            if errors:
                failures.append({"index": index, "errors": errors})
                continue
            obs = observed(grid)
            profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
            profiles.add(profile)
            profile_names.add(obs["component_profile"])
            colors.add(obs["distractor_color"])
            ranks.add(largest_scan_rank(grid))
            exact_hits += profile in CANONICAL_PROFILES
            intended = reference_output(grid)
            rival_disagreements["first"] += recolor_rank(grid, 0) != intended
            rival_disagreements["last"] += recolor_rank(grid, -1) != intended
            rival_disagreements["smallest"] += recolor_smallest(grid) != intended
            rival_disagreements["largest_bbox_area"] += recolor_largest_bbox(grid) != intended
            hashes.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
        report["bands"][band] = {
            "samples": count,
            "failures": failures,
            "distinct_inputs": len(hashes),
            "profiles": sorted(profiles),
            "component_profiles": sorted(profile_names),
            "largest_scan_ranks": sorted(ranks),
            "distractor_colors": sorted(colors),
            "canonical_profile_hits": exact_hits,
            "rival_disagreements": rival_disagreements,
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=256)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report = audit(module, args.count)
    source = Path(args.generator or ROOT / f"generators/{TASK_ID}/generator.py")
    report["generator_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    bad = report["rule_hash"] != EXPECTED_RULE_HASH
    bad |= any(item["self_check"] or item["strict"] or not item["oracle_matches"] for item in report["canonical"])
    bad |= any(data["failures"] or not data["canonical_profile_hits"] for data in report["bands"].values())
    return int(bad)


if __name__ == "__main__":
    raise SystemExit(main())
