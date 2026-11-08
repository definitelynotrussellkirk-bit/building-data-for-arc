from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "7e52d15790d7"
mod = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = find_root(__file__)


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 0 or (sr, sc) in seen:
                continue
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
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append(cells)
    return out


def _perimeter(cells):
    cells = set(cells)
    return sum(
        (r + dr, c + dc) not in cells
        for r, c in cells
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
    )


def _bbox_perimeter(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return 2 * (
        max(rows) - min(rows) + 1 + max(cols) - min(cols) + 1
    )


def _canonical_inputs():
    return [pair["input"] for pair in canonical_pairs(TASK_ID, root=ROOT)]


def test_rule_hash_and_summary_name_true_perimeter():
    assert mod.RULE_HASH == "50de31dd583a"
    text = (mod.__doc__ or "") + " " + mod.SUMMARY
    assert "true 4-neighbor" in text
    assert "sort blobs by bbox perimeter" not in text.lower()


def test_canonical_inputs_pass_structural_self_check():
    for grid in _canonical_inputs():
        assert mod.self_check(copy.deepcopy(grid)) == []


def test_three_demo_schedule_refutes_bbox_area_and_position_shortcuts():
    grids = [mod.generate(101, i, difficulty="medium") for i in range(3)]
    observations = [mod.observe_overrides(grid) for grid in grids]
    assert {item["shape_profile"] for item in observations} == {
        "bbox_tie",
        "area_inversion",
        "canonical_varied",
    }
    assert all(item["sort_changes_left_to_right"] for item in observations)
    assert any(item["bbox_sort_disagrees"] for item in observations)
    assert any(item["area_sort_disagrees"] for item in observations)


def test_declared_dimension_boundaries_are_exact_in_every_band():
    for band in ("easy", "medium", "hard"):
        for h, w in ((9, 12), (14, 18)):
            grid = mod.generate(
                13,
                7,
                difficulty=band,
                grid_h=h,
                grid_w=w,
            )
            assert (len(grid), len(grid[0])) == (h, w)


def test_self_check_rejects_four_targeted_impostors():
    base = mod.generate(37, 0, difficulty="medium")
    assert mod.self_check(base) == []
    comps = _components(base)
    by_perim = sorted(comps, key=_perimeter, reverse=True)

    # 1. Duplicate a component color while keeping components separate.
    duplicate_color = copy.deepcopy(base)
    src_color = duplicate_color[by_perim[0][0][0]][by_perim[0][0][1]]
    for r, c in by_perim[1]:
        duplicate_color[r][c] = src_color
    assert mod.self_check(duplicate_color)

    # 2. Make one component multicolor without altering its geometry.
    multicolor = copy.deepcopy(base)
    r, c = by_perim[0][0]
    multicolor[r][c] = 9 if multicolor[r][c] != 9 else 8
    assert mod.self_check(multicolor)

    # 3. Remove a leaf cell, destroying the required perimeter support.
    wrong_perimeter = copy.deepcopy(base)
    removable = None
    comp_set = set(by_perim[0])
    for r, c in by_perim[0]:
        degree = sum(
            (r + dr, c + dc) in comp_set
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
        )
        if degree == 1:
            removable = (r, c)
            break
    assert removable is not None
    wrong_perimeter[removable[0]][removable[1]] = 0
    assert mod.self_check(wrong_perimeter)

    # 4. Join two components with a colored horizontal bridge.
    merged = copy.deepcopy(base)
    left, right = sorted(comps, key=lambda cells: min(c for _, c in cells))[:2]
    lr, lc = min(left, key=lambda p: abs(p[0] - right[0][0]) - p[1])
    rr, rc = min(right, key=lambda p: abs(p[0] - lr) + p[1])
    # Use a simple Manhattan path; any resulting malformed scene must reject.
    color = merged[lr][lc]
    r, c = lr, lc
    while c != rc:
        c += 1 if rc > c else -1
        merged[r][c] = color
    while r != rr:
        r += 1 if rr > r else -1
        merged[r][c] = color
    assert mod.self_check(merged)


def test_true_perimeter_observable_is_not_bbox_perimeter():
    grid = mod.generate(5, 0, difficulty="hard", shape_profile="bbox_tie")
    comps = _components(grid)
    assert sorted((_perimeter(c) for c in comps), reverse=True) == [12, 10, 8]
    assert len({_bbox_perimeter(c) for c in comps}) < 3
