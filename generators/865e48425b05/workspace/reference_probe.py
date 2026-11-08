"""Independent oracle and review helpers for task 865e48425b05.

This module deliberately does not import implementation helpers from generator.py.
The canonical Racket rule remains label authority; ``reference_output`` is a
small independent mirror used for regression and parity checks.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
from typing import Iterable

TASK_ID = "865e48425b05"
HOME = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))

# Desired exact mask-id contract, duplicated independently from production.
MASKS: tuple[frozenset[tuple[int, int]], ...] = (
    frozenset({(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)}),
    frozenset({(0, 0), (1, 0), (1, 1), (1, 2), (2, 2)}),
    frozenset({(0, 0), (0, 1), (0, 2), (1, 2), (2, 1), (2, 2)}),
    frozenset({(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)}),
    frozenset({(0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0)}),
    frozenset({(0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2)}),
    frozenset({(0, 0), (1, 0), (1, 1)}),
    frozenset({(0, 0), (0, 1), (0, 2), (1, 1)}),
    frozenset({(0, 0), (0, 1), (1, 1), (1, 2)}),
    frozenset({(0, 0), (1, 0), (1, 1), (2, 0)}),
    frozenset({(0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3)}),
    frozenset({(0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 1), (3, 2)}),
)

CANONICAL_PROFILES = {
    (7, 9, 3),
    (8, 10, 2),
    (9, 12, 4),
    (7, 11, 3),
    (9, 13, 4),
}


def load_generator(path: str | Path | None = None):
    source = Path(path or HOME / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_865e48425b05", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    from reviewer_support import canonical_pairs as read_pairs, find_root

    return read_pairs(TASK_ID, root=find_root(__file__))


def palette(grid: list[list[int]]) -> list[int]:
    return [value for value in grid[0] if value != 0]


def normalized_mask(grid: list[list[int]]) -> frozenset[tuple[int, int]]:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    if not cells:
        raise ValueError("grid has no color-1 mask")
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def mask_shape(grid: list[list[int]]) -> tuple[int, int]:
    cells = normalized_mask(grid)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def mask_id(grid: list[list[int]]) -> int:
    shape = normalized_mask(grid)
    try:
        return MASKS.index(shape)
    except ValueError as exc:
        raise ValueError(f"unrecognized normalized mask: {sorted(shape)}") from exc


def _pack(mask: Iterable[tuple[int, int]], colors: list[int], *, gap: int = 1,
          forced_shape: tuple[int, int] | None = None, solid: bool = False) -> list[list[int]]:
    cells = set(mask)
    if forced_shape is None:
        mh = max(r for r, _ in cells) + 1
        mw = max(c for _, c in cells) + 1
    else:
        mh, mw = forced_shape
        cells = {(r, c) for r, c in cells if 0 <= r < mh and 0 <= c < mw}
    if solid:
        cells = {(r, c) for r in range(mh) for c in range(mw)}
    out_w = len(colors) * mw + max(0, len(colors) - 1) * gap
    out = [[0] * out_w for _ in range(mh)]
    for index, color in enumerate(colors):
        left = index * (mw + gap)
        for r, c in cells:
            out[r][left + c] = color
    return out


def reference_output(grid: list[list[int]]) -> list[list[int]]:
    return _pack(normalized_mask(grid), palette(grid))


def sorted_palette_rival(grid: list[list[int]]) -> list[list[int]]:
    return _pack(normalized_mask(grid), sorted(palette(grid)))


def fixed_3x3_rival(grid: list[list[int]]) -> list[list[int]]:
    return _pack(normalized_mask(grid), palette(grid), forced_shape=(3, 3))


def no_gap_rival(grid: list[list[int]]) -> list[list[int]]:
    return _pack(normalized_mask(grid), palette(grid), gap=0)


def solid_bbox_rival(grid: list[list[int]]) -> list[list[int]]:
    return _pack(normalized_mask(grid), palette(grid), solid=True)


def observed_axes(grid: list[list[int]]) -> dict[str, int]:
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_palette": len(palette(grid)),
        "mask_id": mask_id(grid),
    }


def canonical_profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len(palette(grid))


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    """Apply the selected canonical Racket authority through the public API."""
    from arcpuzzles import Catalog
    from reviewer_support import find_root

    receipt = Catalog(find_root(__file__)).apply(TASK_ID, deepcopy(grids), timeout=180)
    if not receipt.get("rule_hash_matches_catalog"):
        raise RuntimeError("catalog application did not use the selected rule hash")
    results = receipt.get("results") or []
    if len(results) != len(grids):
        raise RuntimeError(f"Racket returned {len(results)} outputs for {len(grids)} inputs")
    errors = [row.get("error") for row in results if row.get("error")]
    if errors:
        raise RuntimeError(f"Racket application errors: {errors[:3]}")
    return [row["output"] for row in results]
