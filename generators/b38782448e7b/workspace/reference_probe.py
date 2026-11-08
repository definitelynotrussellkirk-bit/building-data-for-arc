"""Independent oracle and adversarial probes for ARC task b38782448e7b.

The canonical Racket program remains authoritative.  This task-local module
spells the rule independently so regression tests can expose shortcuts and
retain exact, inspectable counterexamples.
"""
from __future__ import annotations

from collections import Counter
import importlib.util
import json
import os
from pathlib import Path
from typing import Any

TASK = "b38782448e7b"
ROOT = Path(__file__).resolve().parents[3]


def load_generator(path: str | os.PathLike[str] | None = None):
    candidate = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", candidate)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {candidate}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    from reviewer_support import canonical_pairs as load_pairs, find_root

    return load_pairs(TASK, root=find_root(__file__), labeled_only=True)


def background(grid: list[list[int]]) -> int:
    counts = Counter(value for row in grid for value in row)
    top = counts.most_common()
    if not top or (len(top) > 1 and top[0][1] == top[1][1]):
        raise ValueError("grid has no unique modal background")
    return top[0][0]


def intended_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent spelling of the top-row, row-1-gated XOR sweep."""
    bg = background(grid)
    out = [list(row) for row in grid]
    if len(grid) < 2:
        return out
    for col, marker in enumerate(grid[0]):
        if marker == bg or marker == grid[1][col]:
            continue
        for row in range(1, len(grid)):
            out[row][col] = bg if grid[row][col] == marker else marker
    return out


def all_top_non_background(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting shortcut: every non-background top cell fires."""
    bg = background(grid)
    out = [list(row) for row in grid]
    for col, marker in enumerate(grid[0]):
        if marker == bg:
            continue
        for row in range(1, len(grid)):
            out[row][col] = bg if grid[row][col] == marker else marker
    return out


def erase_unmarked_body(grid: list[list[int]]) -> list[list[int]]:
    """Historical generated-distribution shortcut: discard all other body art."""
    bg = background(grid)
    out = [[bg for _ in row] for row in grid]
    out[0] = list(grid[0])
    if len(grid) < 2:
        return out
    for col, marker in enumerate(grid[0]):
        if marker == bg or marker == grid[1][col]:
            continue
        for row in range(1, len(grid)):
            out[row][col] = bg if grid[row][col] == marker else marker
    return out


def binary_toggle_only(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: preserve third colours instead of overwriting them."""
    bg = background(grid)
    out = [list(row) for row in grid]
    if len(grid) < 2:
        return out
    for col, marker in enumerate(grid[0]):
        if marker == bg or marker == grid[1][col]:
            continue
        for row in range(1, len(grid)):
            if grid[row][col] == marker:
                out[row][col] = bg
            elif grid[row][col] == bg:
                out[row][col] = marker
    return out


def solid_paint_columns(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: paint marker columns solid and never perform XOR-off."""
    bg = background(grid)
    out = [list(row) for row in grid]
    if len(grid) < 2:
        return out
    for col, marker in enumerate(grid[0]):
        if marker == bg or marker == grid[1][col]:
            continue
        for row in range(1, len(grid)):
            out[row][col] = marker
    return out


def observed(grid: list[list[int]]) -> dict[str, int]:
    bg = background(grid)
    markers = [
        c for c, value in enumerate(grid[0])
        if value != bg and len(grid) > 1 and value != grid[1][c]
    ]
    decoys = [
        c for c, value in enumerate(grid[0])
        if value != bg and len(grid) > 1 and value == grid[1][c]
    ]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "bg_color": bg,
        "palette_size": len({value for row in grid for value in row}),
        "n_markers": len(markers),
        "n_decoys": len(decoys),
    }


def firing_columns(grid: list[list[int]]) -> list[int]:
    bg = background(grid)
    return [
        c for c, value in enumerate(grid[0])
        if value != bg and value != grid[1][c]
    ]


def witness_flags(grid: list[list[int]]) -> dict[str, bool]:
    bg = background(grid)
    markers = firing_columns(grid)
    marker_set = set(markers)
    decoys = [
        c for c, value in enumerate(grid[0])
        if value != bg and value == grid[1][c]
    ]
    return {
        "non_firing_top_decoy": any(
            any(grid[r][c] != grid[0][c] for r in range(2, len(grid)))
            for c in decoys
        ),
        "unmarked_body_preservation": any(
            grid[r][c] != bg
            for r in range(1, len(grid))
            for c in range(len(grid[0]))
            if c not in marker_set
        ),
        "third_color_overwrite": any(
            grid[r][c] not in (bg, grid[0][c])
            for c in markers
            for r in range(1, len(grid))
        ),
        "xor_off_marker_match": any(
            grid[r][c] == grid[0][c]
            for c in markers
            for r in range(1, len(grid))
        ),
    }


def decoy_witness() -> list[list[int]]:
    """Exact lawful 20x20 counterexample to the all-top shortcut."""
    bg = 8
    grid = [[bg] * 20 for _ in range(20)]
    # Firing marker 2 in column 3.  It sees all three body categories.
    grid[0][3] = 2
    grid[1][3] = 4
    grid[2][3] = 2
    grid[3][3] = bg
    grid[4][3] = 4
    # Firing marker 4 in column 8.
    grid[0][8] = 4
    grid[1][8] = bg
    grid[2][8] = 4
    grid[3][8] = 2
    # Non-firing top decoy: row 0 equals row 1.
    grid[0][13] = 2
    grid[1][13] = 2
    grid[2][13] = bg
    grid[3][13] = 4
    # Preserved body content outside firing marker columns.
    for r in (10, 11):
        for c in (15, 16):
            grid[r][c] = 4
    return grid


def changed_cells(left: list[list[int]], right: list[list[int]]) -> list[tuple[int, int, int, int]]:
    return [
        (r, c, left[r][c], right[r][c])
        for r in range(len(left))
        for c in range(len(left[0]))
        if left[r][c] != right[r][c]
    ]


def audit(module=None, *, per_band: int = 50) -> dict[str, Any]:
    gen = module or load_generator()
    rivals = {
        "all_top_non_background": all_top_non_background,
        "erase_unmarked_body": erase_unmarked_body,
        "binary_toggle_only": binary_toggle_only,
        "solid_paint_columns": solid_paint_columns,
    }
    report: dict[str, Any] = {
        "schema": "b38782448e7b-independent-audit-v1",
        "task": TASK,
        "canonical": {},
        "bands": {},
    }
    pairs = canonical_pairs()
    report["canonical"] = {
        "pairs": len(pairs),
        "oracle_matches": sum(intended_output(p["input"]) == p["output"] for p in pairs),
        "shortcut_fit": {
            name: sum(rival(p["input"]) == p["output"] for p in pairs)
            for name, rival in rivals.items()
        },
    }
    for band in (None, "easy", "medium", "hard"):
        grids = [gen.generate(1701 + i, i, difficulty=band) for i in range(per_band)]
        report["bands"][str(band)] = {
            "samples": len(grids),
            "self_check_failures": sum(bool(gen.self_check(grid)) for grid in grids),
            "distinct_inputs": len({json.dumps(grid, separators=(",", ":")) for grid in grids}),
            "profiles": sorted({
                (len(grid), len(grid[0]), len({v for row in grid for v in row}))
                for grid in grids
            }),
            "witness_counts": {
                name: sum(witness_flags(grid)[name] for grid in grids)
                for name in witness_flags(grids[0])
            },
            "rival_disagreements": {
                name: sum(rival(grid) != intended_output(grid) for grid in grids)
                for name, rival in rivals.items()
            },
        }
    return report


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
