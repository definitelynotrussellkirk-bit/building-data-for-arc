"""Native parametric family for ARC task fa3e0c305476.

The default is the byte-exact canonical rule.  The alternate retains the same
cyan-frame/hole-count reasoning but adds an input-dependent relay:

1. count the non-cyan regions in the row-major first cyan object;
2. use that count as the episode input's selector;
3. recolor only objects whose own region count matches the selector.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "fa3e0c305476"
SCOPES = ("all_objects", "anchor_hole_matches")
DEFAULT_SCOPE = "all_objects"
COLOR_BY_COUNT = {1: 1, 2: 2, 3: 3, 4: 7}
CARD = ((1, 0), (-1, 0), (0, 1), (0, -1))

CANONICAL_PROGRAM = Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8").rstrip("\n")
MATCH_PROGRAM = """(rule! (lambda (g)
  (let* ((objs (objects g 0))
         (anchor (first objs))
         (anchor-count
           (with-bbox anchor (ar1 ac1 ar2 ac2)
             (length (objects (subgrid g ar1 ac1 ar2 ac2) 8)))))
    (paint-objects-by g objs
      (lambda (obj)
        (with-bbox obj (r1 c1 r2 c2)
          (let* ((sub (subgrid g r1 c1 r2 c2))
                 (n-holes (length (objects sub 8))))
            (if (= n-holes anchor-count)
                (casev n-holes {1 1 2 2 3 3 4 7} (obj-color obj))
                (obj-color obj)))))))))"""
SECOND_ANCHOR_PROGRAM = """(rule! (lambda (g)
  (let* ((objs (objects g 0))
         (wrong-anchor (second objs))
         (anchor-count
           (with-bbox wrong-anchor (ar1 ac1 ar2 ac2)
             (length (objects (subgrid g ar1 ac1 ar2 ac2) 8)))))
    (paint-objects-by g objs
      (lambda (obj)
        (with-bbox obj (r1 c1 r2 c2)
          (let* ((sub (subgrid g r1 c1 r2 c2))
                 (n-holes (length (objects sub 8))))
            (if (= n-holes anchor-count)
                (casev n-holes {1 1 2 2 3 3 4 7} (obj-color obj))
                (obj-color obj)))))))))"""

# height, width, ordered hole counts.  Index zero is always placed top-left.
_DEMO_SPECS = (
    (14, 26, (1, 1, 2, 4)),
    (14, 26, (3, 2, 3, 4)),
    (18, 28, (2, 0, 2, 4, 5)),
    (18, 28, (4, 1, 3, 4, 6)),
    (18, 28, (1, 2, 1, 3, 5)),
    (22, 30, (3, 1, 2, 3, 4, 6)),
)
_QUERY_SPECS = (
    (16, 26, (2, 3, 2, 1)),
    (18, 28, (4, 2, 3, 4, 5)),
    (20, 30, (1, 4, 1, 2, 6)),
    (30, 30, (3, 1, 3, 2, 4, 5)),
)


def validate_settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"recolor_scope"}:
        raise ValueError("settings must contain exactly recolor_scope")
    scope = settings["recolor_scope"]
    if type(scope) is not str or scope not in SCOPES:
        raise ValueError(f"recolor_scope must be one of {SCOPES}")
    return {"recolor_scope": scope}


def rule_text(scope: str) -> str:
    if scope == "all_objects":
        return CANONICAL_PROGRAM
    if scope == "anchor_hole_matches":
        return MATCH_PROGRAM
    raise ValueError(f"unknown recolor_scope {scope!r}")


def counterfactual_program() -> str:
    return SECOND_ANCHOR_PROGRAM


def _mix(*parts: object) -> int:
    text = ":".join(map(str, (TASK_ID, "anchor-hole-relay-v1", *parts)))
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")


def _lattice_frame(
    hole_count: int,
    hole_rows: int,
    hole_cols: int,
    hole_h: int,
    hole_w: int,
) -> tuple[frozenset[tuple[int, int]], int, int]:
    if hole_rows * hole_cols != hole_count:
        raise ValueError("lattice factorization does not match hole count")
    height = hole_rows * hole_h + hole_rows + 1
    width = hole_cols * hole_w + hole_cols + 1
    holes = {
        (1 + hr * (hole_h + 1) + dr, 1 + hc * (hole_w + 1) + dc)
        for hr in range(hole_rows)
        for hc in range(hole_cols)
        for dr in range(hole_h)
        for dc in range(hole_w)
    }
    cells = frozenset(
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in holes
    )
    return cells, height, width


def _transpose(candidate):
    cells, height, width = candidate
    return frozenset((c, r) for r, c in cells), width, height


def _frame_candidates(hole_count: int, variant: int):
    if type(hole_count) is not int or not 0 <= hole_count <= 6:
        raise ValueError("hole count must be in 0..6")
    if hole_count == 0:
        candidates = []
        for height, width in ((2, 2), (2, 3), (3, 2), (3, 3), (4, 3), (3, 4)):
            cells = frozenset((r, c) for r in range(height) for c in range(width))
            candidates.append((cells, height, width))
    else:
        candidates = []
        for rows in range(1, hole_count + 1):
            if hole_count % rows:
                continue
            cols = hole_count // rows
            for hole_h, hole_w in ((1, 1), (1, 2), (2, 1)):
                candidate = _lattice_frame(hole_count, rows, cols, hole_h, hole_w)
                candidates.extend((candidate, _transpose(candidate)))
    unique = list({(cells, h, w) for cells, h, w in candidates})
    unique.sort(key=lambda item: (item[1] * item[2], max(item[1], item[2]), item[1], item[2], sorted(item[0])))
    shift = variant % len(unique)
    return unique[shift:] + unique[:shift]


def _separated(left, right) -> bool:
    lr0, lc0, lr1, lc1 = left
    rr0, rc0, rr1, rc1 = right
    return (
        lr1 + 1 < rr0
        or rr1 + 1 < lr0
        or lc1 + 1 < rc0
        or rc1 + 1 < lc0
    )


def _positions(height: int, width: int, fh: int, fw: int, *, role: str | None, variant: int):
    if role == "tl":
        return [(0, 0)]
    if role == "tr":
        return [(0, width - fw)]
    if role == "bl":
        return [(height - fh, 0)]
    if role == "br":
        return [(height - fh, width - fw)]

    anchors = [
        (0, width - fw),
        (height - fh, 0),
        (height - fh, width - fw),
        ((height - fh) // 2, (width - fw) // 2),
        (0, (width - fw) // 2),
        (height - fh, (width - fw) // 2),
        ((height - fh) // 2, 0),
        ((height - fh) // 2, width - fw),
    ]
    all_positions = [
        (r, c)
        for r in range(height - fh + 1)
        for c in range(width - fw + 1)
    ]
    rng = random.Random(variant)
    rng.shuffle(anchors)
    rng.shuffle(all_positions)
    result = []
    seen = set()
    for pos in anchors + all_positions:
        if pos not in seen:
            seen.add(pos)
            result.append(pos)
    return result


def _pack(height: int, width: int, counts: tuple[int, ...], seed: int, split: str, index: int):
    roles = ["tl"] + (["tr", "bl", "br"] if (height, width) == (30, 30) else [None, None, None])
    roles.extend([None] * (len(counts) - len(roles)))
    choices = [
        _frame_candidates(count, _mix(seed, split, index, object_index, "shape"))
        for object_index, count in enumerate(counts)
    ]
    placements: list[tuple[frozenset[tuple[int, int]], int, int, int, int] | None] = [None] * len(counts)
    rects: list[tuple[int, int, int, int]] = []

    def search(object_index: int) -> bool:
        if object_index == len(counts):
            return True
        role = roles[object_index]
        for cells, fh, fw in choices[object_index]:
            if fh > height or fw > width:
                continue
            for row, col in _positions(
                height,
                width,
                fh,
                fw,
                role=role,
                variant=_mix(seed, split, index, object_index, fh, fw, "position"),
            ):
                rect = (row, col, row + fh - 1, col + fw - 1)
                if not all(_separated(rect, prior) for prior in rects):
                    continue
                placements[object_index] = (cells, fh, fw, row, col)
                rects.append(rect)
                if search(object_index + 1):
                    return True
                rects.pop()
                placements[object_index] = None
        return False

    if not search(0):
        raise ValueError(f"cannot pack counts {counts} on {height}x{width}")
    return [placement for placement in placements if placement is not None]


def _components(grid, color=8):
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in CARD:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    cells.add(nxt)
                    stack.append(nxt)
        result.append(cells)
    return sorted(result, key=min)


def _regions(cells: Iterable[tuple[int, int]]):
    remaining = set(cells)
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        region = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in CARD:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    region.add(nxt)
                    stack.append(nxt)
        result.append(region)
    return result


def analyze(grid) -> dict[str, Any]:
    objects = []
    for cells in _components(grid):
        r1 = min(r for r, _ in cells)
        c1 = min(c for _, c in cells)
        r2 = max(r for r, _ in cells)
        c2 = max(c for _, c in cells)
        noncyan = {
            (r, c)
            for r in range(r1, r2 + 1)
            for c in range(c1, c2 + 1)
            if grid[r][c] != 8
        }
        objects.append({
            "cells": cells,
            "bbox": (r1, c1, r2, c2),
            "hole_count": len(_regions(noncyan)),
        })
    if not objects:
        raise ValueError("input has no cyan object")
    return {
        "objects": objects,
        "anchor_hole_count": objects[0]["hole_count"],
    }


def apply_scope(grid, scope: str):
    info = analyze(grid)
    anchor_count = info["anchor_hole_count"]
    out = [row[:] for row in grid]
    for obj in info["objects"]:
        count = obj["hole_count"]
        color = COLOR_BY_COUNT.get(count, 8)
        if scope == "anchor_hole_matches" and count != anchor_count:
            color = 8
        elif scope != "all_objects" and scope != "anchor_hole_matches":
            raise ValueError(f"unknown recolor_scope {scope!r}")
        for r, c in obj["cells"]:
            out[r][c] = color
    return out


def apply_second_anchor(grid):
    info = analyze(grid)
    if len(info["objects"]) < 2:
        raise ValueError("counterfactual requires two objects")
    selector = info["objects"][1]["hole_count"]
    out = [row[:] for row in grid]
    for obj in info["objects"]:
        count = obj["hole_count"]
        color = COLOR_BY_COUNT.get(count, 8) if count == selector else 8
        for r, c in obj["cells"]:
            out[r][c] = color
    return out


def _build_input(seed: int, split: str, index: int, spec):
    height, width, counts = spec
    grid = [[0 for _ in range(width)] for _ in range(height)]
    placements = _pack(height, width, counts, seed, split, index)
    for cells, _fh, _fw, top, left in placements:
        for r, c in cells:
            grid[top + r][left + c] = 8
    actual = [obj["hole_count"] for obj in analyze(grid)["objects"]]
    if not actual or actual[0] != counts[0] or sorted(actual) != sorted(counts):
        raise ValueError(
            f"anchor/count drift: expected anchor {counts[0]} and multiset {sorted(counts)}, got {actual}"
        )
    return grid


def _pair(seed: int, split: str, index: int, spec, scope: str):
    grid = _build_input(seed, split, index, spec)
    return {"input": grid, "output": apply_scope(grid, scope)}


def generate_episode(seed: int, *, recolor_scope: str, demos: int, queries: int):
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an integer in 0..2**63-1 (not bool)")
    if recolor_scope not in SCOPES:
        raise ValueError(f"unknown recolor_scope {recolor_scope!r}")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an integer in 1..4")
    train = [
        _pair(seed, "train", index, _DEMO_SPECS[index], recolor_scope)
        for index in range(demos)
    ]
    test = [
        _pair(seed, "test", index, _QUERY_SPECS[index], recolor_scope)
        for index in range(queries)
    ]
    return {
        "train": train,
        "test": test,
        "program_solution": rule_text(recolor_scope),
    }


def public_turn(episode: dict[str, Any], query_index: int = 0):
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index must select a retained query")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def public_bytes(episode: dict[str, Any], query_index: int = 0) -> bytes:
    return (json.dumps(public_turn(episode, query_index), sort_keys=True, separators=(",", ":")) + "\n").encode()


def public_id(episode: dict[str, Any], query_index: int = 0) -> str:
    return hashlib.sha256(public_bytes(episode, query_index)).hexdigest()


def causal_case(seed: int = 0):
    episode = generate_episode(seed, recolor_scope="anchor_hole_matches", demos=6, queries=4)
    pair = next(
        candidate
        for candidate in episode["train"] + episode["test"]
        if len(analyze(candidate["input"])["objects"]) >= 2
        and analyze(candidate["input"])["objects"][0]["hole_count"]
        != analyze(candidate["input"])["objects"][1]["hole_count"]
        and apply_second_anchor(candidate["input"]) != candidate["output"]
    )
    info = analyze(pair["input"])
    wrong = apply_second_anchor(pair["input"])
    return {
        "settings": {"recolor_scope": "anchor_hole_matches"},
        "program": MATCH_PROGRAM,
        "input": deepcopy(pair["input"]),
        "output": deepcopy(pair["output"]),
        "intermediate_value": {
            "anchor_hole_count": info["objects"][0]["hole_count"],
            "wrong_second_object_hole_count": info["objects"][1]["hole_count"],
        },
        "counterfactual_program": SECOND_ANCHOR_PROGRAM,
        "counterfactual_output": wrong,
        "ablation": "wrong_intermediate",
    }
