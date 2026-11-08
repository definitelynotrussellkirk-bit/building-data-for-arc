"""Generator for ``v0_original:easy_01`` — fill hollow-square centers.

The canonical rule changes exactly the zero center of every monochrome 3x3
ring.  Ordinary generated inputs therefore contain one to three target rings
plus a deliberately non-target concave distractor.  The distractor is crucial:
it falsifies shortcuts such as "fill every zero inside a colored bounding box"
while leaving the Racket rule as the sole output authority.
"""
from __future__ import annotations

from itertools import combinations
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ad668d162e0a"
VERSION = "2.0.0"
TASK_ID = "ad668d162e0a"
RULE_HASH = "a3291aba4d90"

SUMMARY = (
    "A 0-background grid contains 1-3 non-overlapping monochrome hollow 3x3 "
    "rings with zero centers.  Each ring uses a distinct color.  A separate "
    "small concave same-palette distractor is not a complete ring and must "
    "remain unchanged.  Fill only each ring center with its ring color."
)

INVARIANTS = [
    "background is 0 and at least two nonzero colors are present",
    "1-3 target motifs are exact monochrome hollow 3x3 rings",
    "target-ring colors are distinct and target windows do not overlap",
    "at least one separate concave non-ring distractor rebuts bbox filling",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
PALETTES = {
    "default": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    "warm": (2, 3, 4, 7, 9),
    "cool": (1, 5, 6, 8),
    "varied": (3, 5, 7, 9),
}

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-linked profile", "valid": "5..10"},
    "grid_w": {"type": "int", "default": "difficulty-linked profile", "valid": "6..12"},
    "n_blocks": {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "palette_kind": {
        "type": "enum",
        "default": "rng helpful",
        "valid": PALETTE_KINDS,
    },
}

# The easy schedule deliberately includes every canonical (height, width,
# target-count) profile.  The separate L distractor supplies the additional
# non-target color needed to rebut bounding-box shortcuts.
_EASY_PROFILES = (
    (5, 7, 1, False),
    (5, 6, 1, False),
    (6, 6, 2, False),
    (7, 6, 2, False),
    (7, 12, 3, False),
)
_MEDIUM_PROFILES = (
    (6, 8, 1, False),
    (7, 9, 2, False),
    (8, 10, 3, False),
    (9, 7, 2, False),
)
_HARD_PROFILES = (
    (8, 10, 1, False),
    (9, 11, 2, False),
    (10, 12, 3, False),
    (10, 9, 2, False),
)

# A 2x2 L has a zero in its bounding box but is not a target ring.  Rotations
# let the placement search use tight canonical-scale canvases.
_DISTRACTOR_VARIANTS = (
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
)


def _ring_border(r0: int, c0: int) -> frozenset[tuple[int, int]]:
    return frozenset(
        (r0 + dr, c0 + dc)
        for dr in range(3)
        for dc in range(3)
        if (dr, dc) != (1, 1)
    )


def _find_rings(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    rings: list[dict[str, Any]] = []
    for r0 in range(h - 2):
        for c0 in range(w - 2):
            center = (r0 + 1, c0 + 1)
            if grid[center[0]][center[1]] != 0:
                continue
            border = _ring_border(r0, c0)
            values = [grid[r][c] for r, c in border]
            if values and values[0] != 0 and all(v == values[0] for v in values):
                rings.append(
                    {
                        "top": r0,
                        "left": c0,
                        "center": center,
                        "border": border,
                        "color": values[0],
                    }
                )
    return rings


def _components(cells: set[tuple[int, int]], grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    """Same-color four-connected components restricted to ``cells``."""
    remaining = set(cells)
    out: list[set[tuple[int, int]]] = []
    while remaining:
        start = remaining.pop()
        color = grid[start[0]][start[1]]
        stack = [start]
        comp = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                p = (r + dr, c + dc)
                if p in remaining and grid[p[0]][p[1]] == color:
                    remaining.remove(p)
                    comp.add(p)
                    stack.append(p)
        out.append(comp)
    return out


def _analysis(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid must be a non-empty list of non-empty rows"]}
    w = len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["grid must be rectangular"]}
    h = len(grid)
    if h > 30 or w > 30:
        errors.append(f"grid exceeds ARC bounds: {h}x{w}")
    bad_values = [
        value
        for row in grid
        for value in row
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
    ]
    if bad_values:
        errors.append("grid contains a non-integer or a color outside 0..9")
        return {"errors": errors, "height": h, "width": w}

    rings = _find_rings(grid)
    if not 1 <= len(rings) <= 3:
        errors.append(f"expected 1..3 hollow 3x3 rings, found {len(rings)}")

    ring_colors = [ring["color"] for ring in rings]
    if len(ring_colors) != len(set(ring_colors)):
        errors.append("target rings must use distinct colors")

    ring_cells: set[tuple[int, int]] = set()
    centers = {ring["center"] for ring in rings}
    for left, right in combinations(rings, 2):
        if left["border"] & right["border"]:
            errors.append("target ring borders overlap")
        if left["center"] in right["border"] or right["center"] in left["border"]:
            errors.append("a target center lies on another target ring")
    for ring in rings:
        ring_cells.update(ring["border"])

    nonzero = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] != 0
    }
    colors = {grid[r][c] for r, c in nonzero}
    if len(colors) < 2:
        errors.append("expected at least two nonzero colors")
    if not any(value == 0 for row in grid for value in row):
        errors.append("background color 0 is absent")

    outside = nonzero - ring_cells
    if len(rings) == 1 and not outside:
        errors.append("single-ring scenes need a non-target distractor")

    distractor_components = _components(outside, grid) if outside else []
    for comp in distractor_components:
        rows = [r for r, _ in comp]
        cols = [c for _, c in comp]
        bh = max(rows) - min(rows) + 1
        bw = max(cols) - min(cols) + 1
        if len(comp) > 7 or bh > 3 or bw > 3:
            errors.append(
                f"non-ring component is too large for the task grammar: "
                f"size={len(comp)} bbox={bh}x{bw}"
            )

    return {
        "errors": errors,
        "height": h,
        "width": w,
        "rings": rings,
        "ring_count": len(rings),
        "ring_colors": ring_colors,
        "ring_cells": ring_cells,
        "centers": centers,
        "outside_cells": outside,
        "distractor_components": distractor_components,
        "colors": colors,
    }


def _has_zero_bbox_hole(info: dict[str, Any], grid: list[list[int]]) -> bool:
    for comp in info.get("distractor_components", []):
        rows = [r for r, _ in comp]
        cols = [c for _, c in comp]
        if any(
            grid[r][c] == 0
            for r in range(min(rows), max(rows) + 1)
            for c in range(min(cols), max(cols) + 1)
        ):
            return True
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural task gate; accepts every canonical input and rejects impostors."""
    return list(_analysis(grid)["errors"])


def _has_capacity(h: int, w: int, n_blocks: int) -> bool:
    """Exact geometry preflight: N disjoint 3x3 windows plus a 2x2-L."""
    positions = [(r, c) for r in range(h - 2) for c in range(w - 2)]
    windows = [(pos, set(_ring_border(*pos)) | {(pos[0] + 1, pos[1] + 1)}) for pos in positions]

    def rec(start: int, chosen: int, occupied: set[tuple[int, int]]) -> bool:
        if chosen == n_blocks:
            for r0 in range(h - 1):
                for c0 in range(w - 1):
                    bbox = {
                        (r0 + dr, c0 + dc)
                        for dr in range(2)
                        for dc in range(2)
                    }
                    if bbox.isdisjoint(occupied):
                        return True
            return False
        for index in range(start, len(windows)):
            _, cells = windows[index]
            if cells.isdisjoint(occupied) and rec(index + 1, chosen + 1, occupied | cells):
                return True
        return False

    return rec(0, 0, set())


def _profiles_for(difficulty: str | None):
    if difficulty == "easy":
        return _EASY_PROFILES
    if difficulty == "hard":
        return _HARD_PROFILES
    return _MEDIUM_PROFILES


def _resolve_dimensions_and_count(ctx, difficulty: str | None, overrides: dict[str, Any]):
    requested_n = int(overrides["n_blocks"]) if overrides.get("n_blocks") is not None else None
    h_overridden = overrides.get("grid_h") is not None
    w_overridden = overrides.get("grid_w") is not None

    if not h_overridden and not w_overridden:
        profiles = [p for p in _profiles_for(difficulty) if requested_n is None or p[2] == requested_n]
        if not profiles:
            profiles = [p for group in (_EASY_PROFILES, _MEDIUM_PROFILES, _HARD_PROFILES) for p in group if p[2] == requested_n]
        profile = ctx.draw_choice("canvas_profile", profiles)
        h = ctx.draw_int("grid_h", profile[0], profile[0])
        w = ctx.draw_int("grid_w", profile[1], profile[1])
        default_n = profile[2]
        reuse = profile[3]
    else:
        h = ctx.draw_int("grid_h", 5, 10) if h_overridden else None
        w = ctx.draw_int("grid_w", 6, 12) if w_overridden else None
        wanted = requested_n or 1
        if h is None:
            choices = [value for value in range(5, 11) if _has_capacity(value, w, wanted)]
            if not choices:
                raise ValueError(f"grid_w={w} cannot support n_blocks={wanted}")
            h = ctx.draw_choice("grid_h", choices)
        if w is None:
            choices = [value for value in range(6, 13) if _has_capacity(h, value, wanted)]
            if not choices:
                raise ValueError(f"grid_h={h} cannot support n_blocks={wanted}")
            w = ctx.draw_choice("grid_w", choices)
        feasible = [n for n in range(1, 4) if _has_capacity(h, w, n)]
        if not feasible:
            raise ValueError(f"grid {h}x{w} cannot support even one ring plus distractor")
        # A single dimension override must remain generatable for every legal boundary.
        # Use the conservative one-ring default unless n_blocks is explicitly requested.
        default_n = 1
        reuse = False

    if requested_n is not None:
        n_blocks = ctx.draw_int("n_blocks", 1, 3)
        if not _has_capacity(h, w, n_blocks):
            raise ValueError(f"grid {h}x{w} is incompatible with n_blocks={n_blocks}")
    else:
        if default_n not in range(1, 4) or not _has_capacity(h, w, default_n):
            feasible = [n for n in range(1, 4) if _has_capacity(h, w, n)]
            default_n = feasible[-1 if difficulty == "hard" else 0]
        n_blocks = ctx.draw_int("n_blocks", default_n, default_n)
    return h, w, n_blocks, reuse


def _candidate_ring_sets(h: int, w: int, n_blocks: int, rng, anchor_mode: str):
    base_candidates = [(r, c) for r in range(h - 2) for c in range(w - 2)]

    def is_border(pos):
        r, c = pos
        return r == 0 or c == 0 or r == h - 3 or c == w - 3

    def is_interior(pos):
        return not is_border(pos)

    seen: set[tuple[tuple[int, int], ...]] = set()
    for _attempt in range(64):
        candidates = list(base_candidates)
        rng.shuffle(candidates)
        if anchor_mode == "border":
            candidates.sort(key=lambda pos: not is_border(pos))
        elif anchor_mode == "interior" and any(is_interior(pos) for pos in candidates):
            candidates.sort(key=lambda pos: not is_interior(pos))

        chosen: list[tuple[int, int]] = []
        occupied: set[tuple[int, int]] = set()

        def rec(start: int):
            if len(chosen) == n_blocks:
                # anchor_mode orders preferred placements but is deliberately not a
                # hard constraint: override boundaries must never become impossible.
                return list(chosen)
            for index in range(start, len(candidates)):
                pos = candidates[index]
                cells = set(_ring_border(*pos)) | {(pos[0] + 1, pos[1] + 1)}
                if not cells.isdisjoint(occupied):
                    continue
                chosen.append(pos)
                occupied.update(cells)
                found = rec(index + 1)
                if found is not None:
                    return found
                chosen.pop()
                occupied.difference_update(cells)
            return None

        found = rec(0)
        if found is None:
            continue
        key = tuple(sorted(found))
        if key not in seen:
            seen.add(key)
            yield found


def _place_scene(h: int, w: int, n_blocks: int, palette_kind: str, reuse_distractor_color: bool, rng, sample_index: int):
    palette = list(PALETTES[palette_kind])
    ring_colors = rng.sample(palette, n_blocks)
    remaining = [color for color in palette if color not in ring_colors]
    distractor_color = ring_colors[0] if reuse_distractor_color or not remaining else rng.choice(remaining)
    anchor_mode = ("border", "interior", "mixed")[sample_index % 3]

    for positions in _candidate_ring_sets(h, w, n_blocks, rng, anchor_mode):
        base = full_grid(h, w, 0)
        occupied: set[tuple[int, int]] = set()
        for color, (r0, c0) in zip(ring_colors, positions):
            border = _ring_border(r0, c0)
            occupied.update(border)
            occupied.add((r0 + 1, c0 + 1))
            for r, c in border:
                base[r][c] = color

        distractor_candidates = [
            (r0, c0, variant)
            for r0 in range(h - 1)
            for c0 in range(w - 1)
            for variant in _DISTRACTOR_VARIANTS
        ]
        rng.shuffle(distractor_candidates)
        for r0, c0, variant in distractor_candidates:
            cells = {(r0 + dr, c0 + dc) for dr, dc in variant}
            if not cells.isdisjoint(occupied):
                continue
            if distractor_color in ring_colors:
                same_color_ring_cells = {
                    (r, c)
                    for color, pos in zip(ring_colors, positions)
                    if color == distractor_color
                    for r, c in _ring_border(*pos)
                }
                if any(
                    (r + dr, c + dc) in same_color_ring_cells
                    for r, c in cells
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                ):
                    continue
            grid = [row[:] for row in base]
            for r, c in cells:
                grid[r][c] = distractor_color
            info = _analysis(grid)
            if (
                not info["errors"]
                and info["ring_count"] == n_blocks
                and _has_zero_bbox_hole(info, grid)
            ):
                return grid
    raise ValueError(
        f"could not realize {n_blocks} rings plus a concave distractor on {h}x{w}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h, w, n_blocks, reuse = _resolve_dimensions_and_count(ctx, difficulty, overrides)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    grid = _place_scene(
        h,
        w,
        n_blocks,
        palette_kind,
        reuse,
        ctx.draw_rng("layout"),
        sample_index,
    )
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("constructed invalid scene: " + "; ".join(errors))
    return grid


def observe_overrides(grid) -> dict[str, int]:
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(info["errors"]))
    return {
        "grid_h": info["height"],
        "grid_w": info["width"],
        "n_blocks": info["ring_count"],
    }


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


MIN_STRICT_FRAC = 0.95


def _lawful_info(grid):
    info = _analysis(grid)
    return None if info["errors"] else info


def _witness(predicate: Callable[[dict[str, Any]], bool], grid) -> bool:
    info = _lawful_info(grid)
    return False if info is None else bool(predicate(info))


SEMANTIC_WITNESSES = {
    "target_ring_present": lambda grid: _witness(lambda info: info["ring_count"] >= 1, grid),
    "shortcut_rebutting_distractor": lambda grid: (
        (info := _lawful_info(grid)) is not None
        and _has_zero_bbox_hole(info, grid)
    ),
    "border_anchored_target": lambda grid: _witness(
        lambda info: any(
            ring["top"] == 0
            or ring["left"] == 0
            or ring["top"] == info["height"] - 3
            or ring["left"] == info["width"] - 3
            for ring in info["rings"]
        ),
        grid,
    ),
    "interior_target": lambda grid: _witness(
        lambda info: any(
            0 < ring["top"] < info["height"] - 3
            and 0 < ring["left"] < info["width"] - 3
            for ring in info["rings"]
        ),
        grid,
    ),
}


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python test mirror; canonical Racket remains authoritative."""
    out = [row[:] for row in grid]
    for ring in _find_rings(grid):
        r, c = ring["center"]
        out[r][c] = ring["color"]
    return out


def _identity(grid):
    return [row[:] for row in grid]


def _fill_component_bboxes(grid):
    """Shortcut competitor: fill every zero inside each color-component bbox."""
    out = [row[:] for row in grid]
    cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0}
    for comp in _components(cells, grid):
        color = grid[next(iter(comp))[0]][next(iter(comp))[1]]
        rows = [r for r, _ in comp]
        cols = [c for _, c in comp]
        for r in range(min(rows), max(rows) + 1):
            for c in range(min(cols), max(cols) + 1):
                if out[r][c] == 0:
                    out[r][c] = color
    return out


_LESSON_COMPETITORS = {
    "copy input unchanged": _identity,
    "fill every colored component bounding box": _fill_component_bboxes,
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} is missing input/output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"{role} is not lawful: {errors[0]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"{role} output disagrees with hollow-ring filling")
    if reasons:
        return reasons

    for name, competitor in _LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"demos do not falsify shortcut '{name}', which changes the query")
    return reasons
