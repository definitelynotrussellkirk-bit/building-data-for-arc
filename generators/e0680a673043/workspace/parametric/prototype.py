"""Episode-level rank-policy family for e0680a673043.

Step A removes the two header commands, ranks the input-dependent objects under
one episode-fixed policy, and selects the one-based k-th object.  The selected
object (cells, color, and bounding box) is the intermediate.  Step B tightly
crops exactly that intermediate and applies the command transform.  The default
``size_desc`` program is byte-for-byte the selected canonical Racket source.
"""
from __future__ import annotations

from collections import deque
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from reviewer_support import canonical_path, find_root

TASK_ID = "e0680a673043"
RANK_POLICIES = ("size_desc", "size_asc", "color_asc")
DEFAULT_POLICY = "size_desc"
ROOT = find_root(__file__)


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")


def _validate_policy(rank_policy: str) -> None:
    if type(rank_policy) is not str or rank_policy not in RANK_POLICIES:
        raise ValueError(f"rank_policy must be one of {RANK_POLICIES}")


def _validate_counts(demos: int, queries: int) -> None:
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")


def canonical_source(*, root: Path = ROOT) -> str:
    sources: list[str] = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if type(source) is not str or not source.strip():
                    raise ValueError("canonical record has no Racket program")
                sources.append(source)
    if not sources or len(set(sources)) != 1:
        raise ValueError("expected one unique canonical Racket program")
    return sources[0]


_CANONICAL_COMPARATOR = """(lambda (a b)
                       (if (= (obj-size a) (obj-size b))
                           (< (obj-color a) (obj-color b))
                           (> (obj-size a) (obj-size b))))"""

_SIZE_ASC_COMPARATOR = """(lambda (a b)
                       (if (= (obj-size a) (obj-size b))
                           (< (obj-color a) (obj-color b))
                           (< (obj-size a) (obj-size b))))"""

_COLOR_ASC_COMPARATOR = """(lambda (a b)
                       (if (= (obj-color a) (obj-color b))
                           (> (obj-size a) (obj-size b))
                           (< (obj-color a) (obj-color b))))"""


def program_for(rank_policy: str = DEFAULT_POLICY, *, root: Path = ROOT) -> str:
    _validate_policy(rank_policy)
    source = canonical_source(root=root)
    if rank_policy == DEFAULT_POLICY:
        return source
    if source.count(_CANONICAL_COMPARATOR) != 1:
        raise ValueError("canonical comparator no longer matches guarded template")
    replacement = (
        _SIZE_ASC_COMPARATOR if rank_policy == "size_asc" else _COLOR_ASC_COMPARATOR
    )
    return source.replace(_CANONICAL_COMPARATOR, replacement)


def _rng(seed: int, label: str) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|rank-family-v1|{seed}|{label}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _normalize(cells: list[tuple[int, int]]) -> list[tuple[int, int]]:
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return sorted((r - r0, c - c0) for r, c in cells)


def _grow_polyomino(rng: random.Random, size: int, max_h: int, max_w: int) -> list[tuple[int, int]]:
    """Grow one connected irregular shape inside a fixed local box."""
    if size < 1 or size > max_h * max_w:
        raise ValueError("invalid polyomino capacity")
    cells = {(max_h // 2, max_w // 2)}
    while len(cells) < size:
        frontier = sorted({
            (r + dr, c + dc)
            for r, c in cells
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            if 0 <= r + dr < max_h and 0 <= c + dc < max_w
            and (r + dr, c + dc) not in cells
        })
        if not frontier:
            raise RuntimeError("polyomino growth exhausted unexpectedly")
        # Prefer frontier cells with one or two occupied neighbours, which keeps
        # the shape connected while avoiding a near-solid rectangle.
        weights = []
        for r, c in frontier:
            neighbours = sum((r + dr, c + dc) in cells for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))
            weights.append(5 if neighbours == 1 else 2 if neighbours == 2 else 1)
        cells.add(rng.choices(frontier, weights=weights, k=1)[0])
    return _normalize(list(cells))


def _d4_variants(cells: list[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    variants: list[list[tuple[int, int]]] = []
    seen = set()
    for mirror in (False, True):
        current = [(r, -c if mirror else c) for r, c in cells]
        for turn in range(4):
            if turn:
                current = [(c, -r) for r, c in current]
            normalized = _normalize(current)
            key = tuple(normalized)
            if key not in seen:
                seen.add(key)
                variants.append(normalized)
    return variants


def _scene_dimensions(index: int, total: int) -> tuple[int, int, bool]:
    if index == total - 1:
        return 30, 30, True
    schedule = ((12, 15), (14, 18), (16, 19), (18, 21), (20, 24), (22, 26), (24, 27), (26, 29), (17, 23))
    h, w = schedule[index % len(schedule)]
    return h, w, False


def _roles(stress: bool) -> list[dict[str, int | str]]:
    if stress:
        specs = (("small", 20, 6, 5), ("medium", 32, 7, 6), ("large", 48, 8, 7))
    else:
        specs = (("small", 5, 3, 3), ("medium", 9, 4, 4), ("large", 14, 5, 4))
    return [
        {"role": role, "size": size, "box_h": bh, "box_w": bw}
        for role, size, bh, bw in specs
    ]


def _build_scene(seed: int, index: int, total: int, *, k: int, cmd: int) -> list[list[int]]:
    h, w, stress = _scene_dimensions(index, total)
    rng = _rng(seed, f"scene:{index}:{total}:{k}:{cmd}")
    grid = [[0 for _ in range(w)] for _ in range(h)]
    grid[0][0] = k
    grid[0][-1] = cmd

    colors = sorted(rng.sample((1, 2, 3, 4, 5, 6, 7, 8, 9), 3))
    # Cross size and color order: medium is lowest color, large is middle,
    # small is highest. Thus k=1 distinguishes all three policies in one scene.
    role_color = {"medium": colors[0], "large": colors[1], "small": colors[2]}
    roles = _roles(stress)
    rng.shuffle(roles)

    lane_w = (w - 2) // 3
    starts = (0, lane_w + 1, 2 * (lane_w + 1))
    for role, left0 in zip(roles, starts):
        cells = _grow_polyomino(
            rng,
            int(role["size"]),
            int(role["box_h"]),
            int(role["box_w"]),
        )
        fits = []
        for candidate in _d4_variants(cells):
            sh = max(r for r, _ in candidate) + 1
            sw = max(c for _, c in candidate) + 1
            if sh <= h - 2 and sw <= lane_w:
                fits.append((candidate, sh, sw))
        if not fits:
            raise RuntimeError("no transformed shape fits its lane")
        shape, sh, sw = rng.choice(fits)
        top = rng.randint(2, h - sh)
        left = left0 + rng.randint(0, lane_w - sw)
        color = role_color[str(role["role"])]
        for dr, dc in shape:
            grid[top + dr][left + dc] = color
    return grid


def _components_same_color(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    result = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        queue = deque([start])
        unseen.remove(start)
        cells = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in unseen and grid[nxt[0]][nxt[1]] == color:
                    unseen.remove(nxt)
                    queue.append(nxt)
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        result.append({
            "color": color,
            "size": len(cells),
            "cells": sorted(cells),
            "r1": min(rows),
            "c1": min(cols),
            "r2": max(rows),
            "c2": max(cols),
        })
    return result


def scene_facts(grid: list[list[int]]) -> dict[str, Any]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    clean = [row[:] for row in grid]
    k, cmd = clean[0][0], clean[0][-1]
    clean[0][0] = 0
    clean[0][-1] = 0
    objects = _components_same_color(clean)
    if len(objects) != 3:
        raise ValueError(f"scene must contain exactly three objects, got {len(objects)}")
    return {"k": k, "cmd": cmd, "clean": clean, "objects": objects}


def select_intermediate(facts: dict[str, Any], rank_policy: str) -> dict[str, Any]:
    _validate_policy(rank_policy)
    objects = list(facts["objects"])
    if rank_policy == "size_desc":
        objects.sort(key=lambda obj: (-obj["size"], obj["color"]))
    elif rank_policy == "size_asc":
        objects.sort(key=lambda obj: (obj["size"], obj["color"]))
    else:
        objects.sort(key=lambda obj: (obj["color"], -obj["size"]))
    k = facts["k"]
    if type(k) is not int or not 1 <= k <= len(objects):
        raise ValueError("rank key does not select an object")
    return dict(objects[k - 1])


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _transform(crop, cmd):
    if cmd == 1:
        return _rotate_cw(crop)
    if cmd == 2:
        return [row[::-1] for row in crop[::-1]]
    if cmd == 3:
        return [row[::-1] for row in crop]
    return [row[:] for row in crop[::-1]]


def python_mirror(grid: list[list[int]], *, rank_policy: str = DEFAULT_POLICY) -> list[list[int]]:
    facts = scene_facts(grid)
    selected = select_intermediate(facts, rank_policy)
    crop = [
        [0 for _ in range(selected["c1"], selected["c2"] + 1)]
        for _ in range(selected["r1"], selected["r2"] + 1)
    ]
    cells = set(selected["cells"])
    for r in range(selected["r1"], selected["r2"] + 1):
        for c in range(selected["c1"], selected["c2"] + 1):
            if (r, c) in cells:
                crop[r - selected["r1"]][c - selected["c1"]] = facts["clean"][r][c]
    return _transform(crop, facts["cmd"])


def generate_claims(
    seed: int,
    rank_policy: str = DEFAULT_POLICY,
    demos: int = 2,
    queries: int = 4,
    *,
    root: Path = ROOT,
) -> dict[str, Any]:
    _validate_seed(seed)
    _validate_policy(rank_policy)
    _validate_counts(demos, queries)
    total = demos + queries
    # The first two demonstrations are deliberately k=1 and k=3.  Crossed
    # size/color orders make the first already separating; the second prevents
    # a one-off color/position coincidence from teaching the family.
    demo_k = (1, 3, 2, 1, 3, 2)
    demo_cmd = (1, 3, 2, 4, 2, 1)
    query_k = (2, 1, 3, 2)
    query_cmd = (2, 4, 1, 3)
    pairs = []
    for index in range(total):
        if index < demos:
            k, cmd = demo_k[index], demo_cmd[index]
        else:
            q = index - demos
            k, cmd = query_k[q], query_cmd[q]
        grid = _build_scene(seed, index, total, k=k, cmd=cmd)
        pairs.append({"input": grid, "output": python_mirror(grid, rank_policy=rank_policy)})
    return {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program_for(rank_policy, root=root),
    }
