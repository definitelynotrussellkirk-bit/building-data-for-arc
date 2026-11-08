"""Generator for v0_original:hard_05 — frames claim enclosed objects.

The selected Racket rule keeps rectangular frame borders, recolors every
monochrome object strictly inside a frame to that frame's color, and erases
objects outside all frames.  The official task uses one hollow 4x4 frame, one
inside color, one outside-decoy color, and a zero background.

Ordinary draws stay close to that manifold while varying exact dimensions,
frame aspect, inside topology, outside-decoy topology, position, and palette.
Every draw contains both decisive effects: at least one visibly recolored
inside object and at least one outside object that must vanish.
"""
from __future__ import annotations

from collections import Counter, deque
from itertools import combinations
from typing import Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "260d8a9d33e6"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "38b85f1dff1d"

SUMMARY = (
    "Build one hollow rectangular frame on a zero background, one or two "
    "same-colored objects strictly inside it, and one differently colored "
    "outside decoy. The oracle keeps the frame, recolors enclosed objects to "
    "the frame color, and erases the outside decoy."
)

INVARIANTS = [
    "background is 0",
    "there is exactly one hollow monochrome rectangular frame",
    "the frame shape is 4x4, 4x5, 5x4, or 5x5",
    "at least one non-frame object is strictly inside the frame",
    "exactly one connected outside-decoy object lies outside the frame bbox",
    "all inside objects share one color and the outside decoy uses another",
    "frame, inside, and outside colors are pairwise distinct",
    "inside and outside evidence are both visible in every ordinary draw",
]

COUNTER_HYPOTHESES = [
    "copy the input unchanged",
    "erase outside objects but preserve inside colors",
    "recolor every object, including outside decoys, to the frame color",
    "recolor inside objects but keep outside decoys",
    "fill the complete frame interior instead of recoloring only objects",
    "treat a fixed position, object size, or color as the answer",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware keyed draw",
        "valid": "5..8",
        "doc": "Exact returned grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware keyed draw",
        "valid": "6..10",
        "doc": "Exact returned grid width.",
    },
    "frame_shape": {
        "type": "enum",
        "default": "six-profile schedule anchored to square4",
        "valid": ["square4", "wide", "tall", "square5"],
        "doc": "Exact frame bounding-box shape.",
    },
    "inside_pattern": {
        "type": "enum",
        "default": "three-profile schedule",
        "valid": ["singleton", "connected", "split"],
        "doc": "Exact topology of the enclosed evidence.",
    },
    "outside_pattern": {
        "type": "enum",
        "default": "alternating schedule",
        "valid": ["singleton", "connected"],
        "doc": "Exact topology of the outside decoy.",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 0.20

_FRAME_SHAPES = {
    "square4": (4, 4),
    "wide": (4, 5),
    "tall": (5, 4),
    "square5": (5, 5),
}
_FRAME_SCHEDULE = ("square4", "wide", "square4", "tall", "square4", "square5")
_INSIDE_SCHEDULE = ("singleton", "connected", "split")
_OUTSIDE_SCHEDULE = ("singleton", "connected")
_CANONICAL_DIMS = ((5, 6), (5, 8), (6, 7), (6, 8))
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _freeze(grid: Sequence[Sequence[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(value) for value in row) for row in grid)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    for name, lo, hi in (("grid_h", 5, 8), ("grid_w", 6, 10)):
        value = overrides.get(name)
        if value is not None and (type(value) is not int or not lo <= value <= hi):
            raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")

    for name, options in (
        ("frame_shape", tuple(_FRAME_SHAPES)),
        ("inside_pattern", _INSIDE_SCHEDULE),
        ("outside_pattern", _OUTSIDE_SCHEDULE),
    ):
        value = overrides.get(name)
        if value is not None and value not in options:
            raise ValueError(f"{name} must be one of {options}")


def _effective_overrides(sample_index: int, difficulty, overrides: dict) -> dict:
    """Pin branch coverage without making any axis inert or unobservable."""
    effective = dict(overrides)
    # Preserve canonical-size support in every difficulty band.  The remaining
    # draws still use difficulty-aware keyed dimensions, so hard examples widen
    # without disowning the official manifold.
    if "grid_h" not in effective and "grid_w" not in effective and sample_index % 4 == 0:
        h, w = _CANONICAL_DIMS[(sample_index // 4) % len(_CANONICAL_DIMS)]
        effective["grid_h"] = h
        effective["grid_w"] = w
    effective.setdefault("frame_shape", _FRAME_SCHEDULE[sample_index % len(_FRAME_SCHEDULE)])
    effective.setdefault("inside_pattern", _INSIDE_SCHEDULE[sample_index % len(_INSIDE_SCHEDULE)])
    effective.setdefault("outside_pattern", _OUTSIDE_SCHEDULE[sample_index % len(_OUTSIDE_SCHEDULE)])
    return effective


def _components(grid: Sequence[Sequence[int]]) -> list[dict]:
    """Return monochrome 4-connected nonzero components."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen: set[tuple[int, int]] = set()
    out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            todo = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while todo:
                rr, cc = todo.popleft()
                cells.append((rr, cc))
                for dr, dc in _CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            out.append({"color": color, "cells": tuple(sorted(cells))})
    return out


def _bbox(cells: Sequence[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _border_cells(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r0, c0, r1, c1 = box
    return {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }


def _strictly_inside(inner, outer) -> bool:
    ir0, ic0, ir1, ic1 = inner
    or0, oc0, or1, oc1 = outer
    return or0 < ir0 and oc0 < ic0 and ir1 < or1 and ic1 < oc1


def _boxes_intersect(left, right) -> bool:
    lr0, lc0, lr1, lc1 = left
    rr0, rc0, rr1, rc1 = right
    return not (lr1 < rr0 or rr1 < lr0 or lc1 < rc0 or rc1 < lc0)


def _analyze(grid: Sequence[Sequence[int]]) -> dict:
    comps = _components(grid)
    frames = []
    for comp in comps:
        box = _bbox(comp["cells"])
        r0, c0, r1, c1 = box
        border = _border_cells(box)
        if r1 - r0 >= 2 and c1 - c0 >= 2 and border <= set(comp["cells"]):
            frames.append({**comp, "bbox": box, "border": border})

    inside = []
    outside = []
    crossing = []
    if len(frames) == 1:
        frame = frames[0]
        frame_cells = set(frame["cells"])
        for comp in comps:
            if set(comp["cells"]) == frame_cells:
                continue
            box = _bbox(comp["cells"])
            if _strictly_inside(box, frame["bbox"]):
                inside.append({**comp, "bbox": box})
            elif _boxes_intersect(box, frame["bbox"]):
                crossing.append({**comp, "bbox": box})
            else:
                outside.append({**comp, "bbox": box})

    return {
        "components": comps,
        "frames": frames,
        "inside": inside,
        "outside": outside,
        "crossing": crossing,
    }


def _inside_pattern(inside: Sequence[dict]) -> str | None:
    total = sum(len(comp["cells"]) for comp in inside)
    if len(inside) == 1 and total == 1:
        return "singleton"
    if len(inside) == 1 and 2 <= total <= 3:
        return "connected"
    if len(inside) == 2 and total == 2 and all(len(comp["cells"]) == 1 for comp in inside):
        return "split"
    return None


def _outside_pattern(outside: Sequence[dict]) -> str | None:
    total = sum(len(comp["cells"]) for comp in outside)
    if len(outside) == 1 and total == 1:
        return "singleton"
    if len(outside) == 1 and 2 <= total <= 5:
        return "connected"
    return None


def _frame_shape(frame: dict) -> str | None:
    r0, c0, r1, c1 = frame["bbox"]
    dims = (r1 - r0 + 1, c1 - c0 + 1)
    for name, expected in _FRAME_SHAPES.items():
        if dims == expected:
            return name
    return None


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed scenes and shortcut-hiding impostors."""
    errors = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["grid must be a nonempty list of rows"]
    h = len(grid)
    w = len(grid[0]) if grid[0] else 0
    if not 5 <= h <= 8 or not 6 <= w <= 10:
        errors.append(f"dimensions must be within 5..8 by 6..10, got {h}x{w}")
    if w == 0 or any(len(row) != w for row in grid):
        return errors + ["grid must be rectangular and nonempty"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cell values must be integers in 0..9")
        return errors

    counts = Counter(value for row in grid for value in row)
    colors = set(counts)
    if 0 not in colors:
        errors.append("background color 0 is required")
    if len(colors) != 4:
        errors.append(f"expected exactly four colors including background, got {len(colors)}")
    facts = _analyze(grid)
    if len(facts["frames"]) != 1:
        errors.append(f"expected exactly one rectangular frame, found {len(facts['frames'])}")
        return errors
    frame = facts["frames"][0]
    if set(frame["cells"]) != frame["border"]:
        errors.append("the frame must be hollow: exactly its border cells")
    if _frame_shape(frame) is None:
        errors.append("frame bbox must be 4x4, 4x5, 5x4, or 5x5")
    if facts["crossing"]:
        errors.append("non-frame objects may not touch/cross the frame bbox")
    if not facts["inside"]:
        errors.append("at least one object must be strictly inside the frame")
    if len(facts["outside"]) != 1:
        errors.append(f"expected exactly one outside-decoy object, found {len(facts['outside'])}")
    if _inside_pattern(facts["inside"]) is None:
        errors.append("inside topology must be singleton, connected 2-3 cells, or two split singletons")
    if _outside_pattern(facts["outside"]) is None:
        errors.append("outside topology must be one connected object of 1-5 cells")

    if facts["inside"] and facts["outside"]:
        inside_colors = {comp["color"] for comp in facts["inside"]}
        outside_colors = {comp["color"] for comp in facts["outside"]}
        role_colors = {frame["color"]} | inside_colors | outside_colors
        if len(inside_colors) != 1:
            errors.append("all inside objects must share one color")
        if len(outside_colors) != 1:
            errors.append("the outside decoy must use one color")
        if len(role_colors) != 3:
            errors.append("frame, inside, and outside role colors must be pairwise distinct")

    interior = {
        (r, c)
        for r in range(frame["bbox"][0] + 1, frame["bbox"][2])
        for c in range(frame["bbox"][1] + 1, frame["bbox"][3])
    }
    occupied_inside = {cell for comp in facts["inside"] for cell in comp["cells"]}
    if not (interior - occupied_inside):
        errors.append("the frame interior needs a background gap to refute fill-interior shortcuts")
    return errors


def _inside_candidates(box, pattern: str) -> list[tuple[tuple[int, int], ...]]:
    r0, c0, r1, c1 = box
    interior = [(r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)]
    if pattern == "singleton":
        return [((r, c),) for r, c in interior]
    if pattern == "split":
        return [
            tuple(sorted((a, b)))
            for a, b in combinations(interior, 2)
            if abs(a[0] - b[0]) + abs(a[1] - b[1]) > 1
        ]

    out = []
    cell_set = set(interior)
    for r, c in interior:
        for dr, dc in ((0, 1), (1, 0)):
            cells = ((r, c), (r + dr, c + dc))
            if set(cells) <= cell_set:
                out.append(tuple(sorted(cells)))
        l_shapes = (
            ((r, c), (r + 1, c), (r, c + 1)),
            ((r, c), (r + 1, c), (r + 1, c + 1)),
            ((r, c), (r, c + 1), (r + 1, c + 1)),
            ((r + 1, c), (r, c + 1), (r + 1, c + 1)),
        )
        for cells in l_shapes:
            if set(cells) <= cell_set:
                out.append(tuple(sorted(cells)))
    return sorted(set(out))


def _outside_candidates(h: int, w: int, box, pattern: str) -> list[tuple[tuple[int, int], ...]]:
    r0, c0, r1, c1 = box

    def outside(cell):
        r, c = cell
        return not (r0 <= r <= r1 and c0 <= c <= c1)

    if pattern == "singleton":
        return [((r, c),) for r in range(h) for c in range(w) if outside((r, c))]

    templates = (
        ((0, 0), (0, 1)),
        ((0, 0), (1, 0)),
        ((0, 0), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (0, 1), (1, 1)),
        ((0, 1), (1, 0), (1, 1)),
    )
    candidates = []
    for template in templates:
        th = max(r for r, _ in template) + 1
        tw = max(c for _, c in template) + 1
        for rr in range(h - th + 1):
            for cc in range(w - tw + 1):
                cells = tuple(sorted((rr + r, cc + c) for r, c in template))
                if all(outside(cell) for cell in cells) and not _boxes_intersect(_bbox(cells), box):
                    candidates.append(cells)
    return sorted(set(candidates))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the Racket program is the oracle."""
    _validate_call(difficulty, overrides)
    effective = _effective_overrides(int(sample_index), difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )

    h = ctx.draw_int_diff("grid_h", 5, 8)
    w = ctx.draw_int_diff("grid_w", 6, 10)
    frame_shape = ctx.draw_choice("frame_shape", tuple(_FRAME_SHAPES))
    inside_pattern = ctx.draw_choice("inside_pattern", _INSIDE_SCHEDULE)
    outside_pattern = ctx.draw_choice("outside_pattern", _OUTSIDE_SCHEDULE)
    fh, fw = _FRAME_SHAPES[frame_shape]

    rng = ctx.draw_rng("layout")
    frame_positions = []
    for r0 in range(h - fh + 1):
        for c0 in range(w - fw + 1):
            box = (r0, c0, r0 + fh - 1, c0 + fw - 1)
            if _inside_candidates(box, inside_pattern) and _outside_candidates(h, w, box, outside_pattern):
                frame_positions.append(box)
    if not frame_positions:
        raise ValueError("requested axes leave no lawful frame/object placement")

    prefer_edge = int(sample_index) % 2 == 0
    edge_positions = [
        box
        for box in frame_positions
        if box[0] == 0 or box[1] == 0 or box[2] == h - 1 or box[3] == w - 1
    ]
    interior_positions = [box for box in frame_positions if box not in edge_positions]
    pool = edge_positions if prefer_edge and edge_positions else interior_positions or frame_positions
    box = rng.choice(pool)

    frame_color, inside_color, outside_color = rng.sample(range(1, 10), 3)
    inside_cells = rng.choice(_inside_candidates(box, inside_pattern))
    outside_cells = rng.choice(_outside_candidates(h, w, box, outside_pattern))

    grid = full_grid(h, w, 0)
    for r, c in _border_cells(box):
        grid[r][c] = frame_color
    for r, c in inside_cells:
        grid[r][c] = inside_color
    for r, c in outside_cells:
        grid[r][c] = outside_color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("internal generator invariant failure: " + "; ".join(errors))
    return grid


def semantic_observables(grid):
    facts = _analyze(grid)
    frame = facts["frames"][0] if len(facts["frames"]) == 1 else None
    inside_cells = sum(len(comp["cells"]) for comp in facts["inside"])
    outside_cells = sum(len(comp["cells"]) for comp in facts["outside"])
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "frame_shape": _frame_shape(frame) if frame else None,
        "inside_pattern": _inside_pattern(facts["inside"]),
        "outside_pattern": _outside_pattern(facts["outside"]),
        "frame_count": len(facts["frames"]),
        "inside_components": len(facts["inside"]),
        "inside_cells": inside_cells,
        "outside_components": len(facts["outside"]),
        "outside_cells": outside_cells,
        "frame_touches_edge": bool(
            frame
            and (
                frame["bbox"][0] == 0
                or frame["bbox"][1] == 0
                or frame["bbox"][2] == len(grid) - 1
                or frame["bbox"][3] == len(grid[0]) - 1
            )
        ),
    }


def observe_overrides(grid):
    facts = semantic_observables(grid)
    return {axis: facts[axis] for axis in AXES}


def strict_canonical_like(grid):
    """Accept the official one-frame manifold, including all four pairs."""
    reasons = self_check([list(row) for row in grid])
    if reasons:
        return reasons
    facts = semantic_observables(grid)
    if facts["grid_h"] not in (5, 6):
        reasons.append(f"canonical height is 5 or 6, got {facts['grid_h']}")
    if facts["grid_w"] not in (6, 7, 8):
        reasons.append(f"canonical width is 6, 7, or 8, got {facts['grid_w']}")
    if facts["frame_shape"] != "square4":
        reasons.append(f"canonical frame bbox is 4x4, got {facts['frame_shape']}")
    return reasons


def _single_frame_parts(grid):
    facts = _analyze(grid)
    if len(facts["frames"]) != 1:
        return None
    return facts["frames"][0], facts["inside"], facts["outside"]


def _blank_like(grid):
    return full_grid(len(grid), len(grid[0]), 0)


def _rival_identity(grid):
    return [list(row) for row in grid]


def _rival_erase_outside_only(grid):
    parts = _single_frame_parts(grid)
    if parts is None:
        return [list(row) for row in grid]
    frame, inside, _outside = parts
    out = _blank_like(grid)
    for r, c in frame["cells"]:
        out[r][c] = frame["color"]
    for comp in inside:
        for r, c in comp["cells"]:
            out[r][c] = comp["color"]
    return out


def _rival_keep_outside(grid):
    parts = _single_frame_parts(grid)
    if parts is None:
        return [list(row) for row in grid]
    frame, inside, outside = parts
    out = _blank_like(grid)
    for r, c in frame["cells"]:
        out[r][c] = frame["color"]
    for comp in inside:
        for r, c in comp["cells"]:
            out[r][c] = frame["color"]
    for comp in outside:
        for r, c in comp["cells"]:
            out[r][c] = comp["color"]
    return out


def _rival_recolor_all_objects(grid):
    parts = _single_frame_parts(grid)
    if parts is None:
        return [list(row) for row in grid]
    frame, inside, outside = parts
    out = _blank_like(grid)
    for r, c in frame["cells"]:
        out[r][c] = frame["color"]
    for comp in inside + outside:
        for r, c in comp["cells"]:
            out[r][c] = frame["color"]
    return out


def _rival_fill_frame_interior(grid):
    parts = _single_frame_parts(grid)
    if parts is None:
        return [list(row) for row in grid]
    frame, _inside, _outside = parts
    out = _blank_like(grid)
    r0, c0, r1, c1 = frame["bbox"]
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            out[r][c] = frame["color"]
    return out


SEMANTIC_RIVALS: dict[str, Callable] = {
    "identity": _rival_identity,
    "erase_outside_only": _rival_erase_outside_only,
    "keep_outside": _rival_keep_outside,
    "recolor_all_objects": _rival_recolor_all_objects,
    "fill_frame_interior": _rival_fill_frame_interior,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _visible_inside_recolor(grid):
    parts = _single_frame_parts(grid)
    return bool(parts and any(comp["color"] != parts[0]["color"] for comp in parts[1]))


def _outside_erasure(grid):
    parts = _single_frame_parts(grid)
    return bool(parts and parts[2])


def _interior_background_gap(grid):
    parts = _single_frame_parts(grid)
    if parts is None:
        return False
    frame, inside, _outside = parts
    occupied = {cell for comp in inside for cell in comp["cells"]}
    r0, c0, r1, c1 = frame["bbox"]
    return any(
        (r, c) not in occupied and grid[r][c] == 0
        for r in range(r0 + 1, r1)
        for c in range(c0 + 1, c1)
    )


SEMANTIC_WITNESSES = {
    "visible_inside_recolor": _visible_inside_recolor,
    "outside_erasure": _outside_erasure,
    "interior_background_gap": _interior_background_gap,
    "inside_singleton": lambda grid: semantic_observables(grid)["inside_pattern"] == "singleton",
    "inside_connected": lambda grid: semantic_observables(grid)["inside_pattern"] == "connected",
    "inside_split": lambda grid: semantic_observables(grid)["inside_pattern"] == "split",
    "outside_singleton": lambda grid: semantic_observables(grid)["outside_pattern"] == "singleton",
    "outside_connected": lambda grid: semantic_observables(grid)["outside_pattern"] == "connected",
    "frame_touches_edge": lambda grid: semantic_observables(grid)["frame_touches_edge"],
    "frame_interior_position": lambda grid: not semantic_observables(grid)["frame_touches_edge"],
}

WITNESS_RIVALS = {
    "visible_inside_recolor": ["identity", "erase_outside_only"],
    "outside_erasure": ["keep_outside", "recolor_all_objects"],
    "interior_background_gap": ["fill_frame_interior"],
}


def lesson_identifiable(demos, query):
    """Reject lessons where a named wrong rule survives demos but changes query."""
    reasons = []
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            _freeze(competitor(demo["input"])) == _freeze(demo["output"])
            for demo in demos
        )
        if survives and _freeze(competitor(query["input"])) != _freeze(query["output"]):
            reasons.append(f"competitor {name!r} fits every demo but changes the query")
    return reasons
