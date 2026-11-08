"""Independent geometry oracle and census helpers for 2f8ecb96521c.

This module deliberately does not import implementation helpers from generator.py.
It is used by focused tests and can also be run as a small source-bound audit.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import sys
from typing import Callable

TASK_ID = "2f8ecb96521c"
HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs as _canonical_pairs, find_root  # noqa: E402


@dataclass(frozen=True)
class Rect:
    r1: int
    c1: int
    r2: int
    c2: int
    cells: tuple[tuple[int, int], ...]

    @property
    def h(self) -> int:
        return self.r2 - self.r1 + 1

    @property
    def w(self) -> int:
        return self.c2 - self.c1 + 1

    @property
    def area(self) -> int:
        return len(self.cells)

    @property
    def shape(self) -> str:
        return f"{self.h}x{self.w}"


def load_generator(path: str | os.PathLike[str] | None = None):
    target = Path(path) if path else HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("reviewed_2f8ecb96521c", target)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {target}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    return _canonical_pairs(TASK_ID, root=find_root(HOME), labeled_only=True)


def _rect_components(grid: list[list[int]]) -> list[Rect]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    rects: list[Rect] = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != 4 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == 4):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r1 = min(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            r2 = max(r for r, _ in cells)
            c2 = max(c for _, c in cells)
            rects.append(Rect(r1, c1, r2, c2, tuple(sorted(cells))))
    return rects


def rule_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent mirror of the selected rule, used only for tests/audits."""
    rects = sorted(_rect_components(grid), key=lambda rect: rect.area)
    if len(rects) != 2 or rects[0].area == rects[1].area:
        raise ValueError("expected exactly two distinct-area color-4 components")
    out = deepcopy(grid)
    for rect, color in zip(rects, (1, 2)):
        for r in range(rect.r1 + 1, rect.r2):
            for c in range(rect.c1 + 1, rect.c2):
                out[r][c] = color
    return out


def _projection_rival(grid: list[list[int]], *, axis: str) -> list[list[int]]:
    """Segment by occupied row/column runs rather than 2-D connectivity."""
    h, w = len(grid), len(grid[0])
    occupied = [
        any(grid[r][c] == 4 for r in range(h) for c in range(w)
            if (c if axis == "column" else r) == index)
        for index in range(w if axis == "column" else h)
    ]
    runs: list[tuple[int, int]] = []
    start = None
    for index, present in enumerate(occupied + [False]):
        if present and start is None:
            start = index
        elif not present and start is not None:
            runs.append((start, index - 1))
            start = None
    if len(runs) != 2:
        return deepcopy(grid)
    groups: list[Rect] = []
    for lo, hi in runs:
        cells = [
            (r, c) for r in range(h) for c in range(w)
            if grid[r][c] == 4 and lo <= (c if axis == "column" else r) <= hi
        ]
        r1, r2 = min(r for r, _ in cells), max(r for r, _ in cells)
        c1, c2 = min(c for _, c in cells), max(c for _, c in cells)
        groups.append(Rect(r1, c1, r2, c2, tuple(cells)))
    groups.sort(key=lambda rect: rect.area)
    out = deepcopy(grid)
    for rect, color in zip(groups, (1, 2)):
        for r in range(rect.r1 + 1, rect.r2):
            for c in range(rect.c1 + 1, rect.c2):
                out[r][c] = color
    return out


def column_projection_rival(grid):
    return _projection_rival(grid, axis="column")


def row_projection_rival(grid):
    return _projection_rival(grid, axis="row")


def position_order_rival(grid):
    rects = sorted(_rect_components(grid), key=lambda rect: (rect.r1, rect.c1))
    out = deepcopy(grid)
    for rect, color in zip(rects, (1, 2)):
        for r in range(rect.r1 + 1, rect.r2):
            for c in range(rect.c1 + 1, rect.c2):
                out[r][c] = color
    return out


def same_color_rival(grid):
    out = deepcopy(grid)
    for rect in _rect_components(grid):
        for r in range(rect.r1 + 1, rect.r2):
            for c in range(rect.c1 + 1, rect.c2):
                out[r][c] = 1
    return out


def reverse_area_rival(grid):
    rects = sorted(_rect_components(grid), key=lambda rect: rect.area, reverse=True)
    out = deepcopy(grid)
    for rect, color in zip(rects, (1, 2)):
        for r in range(rect.r1 + 1, rect.r2):
            for c in range(rect.c1 + 1, rect.c2):
                out[r][c] = color
    return out


RIVALS: dict[str, Callable] = {
    "column_projection": column_projection_rival,
    "row_projection": row_projection_rival,
    "position_order": position_order_rival,
    "same_color": same_color_rival,
    "reverse_area": reverse_area_rival,
}


def observed(grid: list[list[int]]) -> dict[str, object]:
    rects = sorted(_rect_components(grid), key=lambda rect: rect.area)
    if len(rects) != 2:
        raise ValueError("expected two rectangles")
    small, large = rects
    row_separated = small.r2 < large.r1 or large.r2 < small.r1
    col_separated = small.c2 < large.c1 or large.c2 < small.c1
    if row_separated and col_separated:
        layout = "diagonal"
        small_near = small.r1 < large.r1 and small.c1 < large.c1
    elif row_separated:
        layout = "stacked"
        small_near = small.r1 < large.r1
    elif col_separated:
        layout = "side_by_side"
        small_near = small.c1 < large.c1
    else:
        raise ValueError("rectangles overlap in both projections")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "small_shape": small.shape,
        "large_shape": large.shape,
        "layout": layout,
        "small_role": "near" if small_near else "far",
    }


def audit(module, draws: int) -> dict:
    by_band: dict[str, dict] = {}
    all_hashes: set[str] = set()
    for band in (None, "easy", "medium", "hard"):
        rows = {
            "draws": 0, "self_check_errors": 0, "oracle_errors": 0,
            "exact_10x10": 0, "layouts": {}, "roles": {},
            "rival_disagreements": {name: 0 for name in RIVALS},
        }
        hashes: set[str] = set()
        for index in range(draws):
            grid = module.generate(101_003 + index, index * 7 + 3, difficulty=band)
            rows["draws"] += 1
            rows["self_check_errors"] += int(bool(module.self_check(grid)))
            try:
                out = rule_output(grid)
                stats = observed(grid)
            except Exception:
                rows["oracle_errors"] += 1
                continue
            rows["exact_10x10"] += int((stats["grid_h"], stats["grid_w"]) == (10, 10))
            rows["layouts"][stats["layout"]] = rows["layouts"].get(stats["layout"], 0) + 1
            rows["roles"][stats["small_role"]] = rows["roles"].get(stats["small_role"], 0) + 1
            for name, rival in RIVALS.items():
                rows["rival_disagreements"][name] += int(rival(grid) != out)
            digest = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
            hashes.add(digest)
            all_hashes.add(digest)
        rows["unique_inputs"] = len(hashes)
        by_band[str(band)] = rows
    return {
        "schema": "2f8ecb96521c-reference-probe-v1",
        "generator_sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        "draws_per_band": draws,
        "unique_inputs_total": len(all_hashes),
        "canonical_pairs": len(canonical_pairs()),
        "canonical_oracle_matches": sum(
            rule_output(pair["input"]) == pair["output"] for pair in canonical_pairs()
        ),
        "by_band": by_band,
        "limits": [
            "Independent Python geometry is supplementary evidence, not selected-Racket parity.",
            "Finite rival counts do not prove universal identifiability.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--draws", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.draws < 1:
        parser.error("--draws must be positive")
    module = load_generator(args.generator)
    report = audit(module, args.draws)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    bad = any(
        row["self_check_errors"] or row["oracle_errors"]
        for row in report["by_band"].values()
    )
    return int(bad or report["canonical_oracle_matches"] != report["canonical_pairs"])


if __name__ == "__main__":
    raise SystemExit(main())
