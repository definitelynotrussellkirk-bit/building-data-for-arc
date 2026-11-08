"""Generator for 372fcf6aa6ad — sort by holes, rotate, and pack.

Each scene contains three to five isolated monochrome objects.  The intended
rule is to crop each object, count enclosed background regions in that crop,
sort by (hole count, object size, top row, left column), rotate every crop 90
degrees clockwise, and horizontally stack the rotated crops with one blank
column between pieces while vertically centering them.

The default sample-index schedule deliberately covers four ordering lessons:
hole-count priority, size tie-breaking, top-row tie-breaking, and left-column
tie-breaking.  Exact overrides remain available for all declared axes.
"""
from __future__ import annotations

from collections import deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "372fcf6aa6ad"
TASK_ID = "372fcf6aa6ad"
VERSION = "3.0.0"
RULE_HASH = "35efb067e49f"

SUMMARY = (
    "A 0-background grid contains 3-5 isolated, distinctly colored objects. "
    "For each object, crop to its bounding box and count enclosed 0-regions. "
    "Sort objects lexicographically by (hole count, nonzero-cell count, bbox "
    "top row, bbox left column), rotate each crop 90 degrees clockwise, then "
    "pack the rotated crops left-to-right with one blank column between them "
    "and vertical center alignment."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0 and every object has one distinct nonzero color",
    "3-5 four-connected objects are separated from other colors even diagonally",
    "normal lessons contain both a hole-free object and an object with holes",
    "objects are sorted by holes, then size, then top row, then left column",
    "each object crop is rotated clockwise before horizontal center-aligned packing",
]

LESSON_PROFILES = (
    "hole_primary",
    "size_secondary",
    "row_tiebreak",
    "col_tiebreak",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed 14..20",
        "valid": "14..20",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed 16..24",
        "valid": "16..24",
    },
    "n": {
        "type": "int",
        "default": "difficulty-skewed 3..5",
        "valid": "3..5",
    },
    "lesson_profile": {
        "type": "str",
        "default": "sample_index cycles all four semantic ordering lessons",
        "valid": "|".join(LESSON_PROFILES),
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIR8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)

# Hand-authored connected motifs.  The families have exactly 0, 1, and 2
# enclosed holes respectively; variants differ in size and asymmetry so that
# neither color nor unrotated texture can shortcut the rule.
_ZERO_HOLE = (
    {(0, 0), (1, 0), (2, 0), (2, 1)},  # canonical-size 4 hook
    {(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)},
    {(0, 0), (0, 1), (0, 2), (1, 1), (2, 1), (2, 2)},
    {(0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2), (3, 3)},
    {(0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2), (3, 3), (2, 3)},
)


def _frame(h: int, w: int) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r in range(h)
        for c in range(w)
        if r in (0, h - 1) or c in (0, w - 1)
    }


_ONE_HOLE = (
    _frame(3, 3),  # canonical-size 8
    _frame(3, 3) | {(1, 3)},
    _frame(3, 4),
    _frame(3, 4) | {(1, 4)},
    _frame(4, 4) | {(1, 4)},
)

# Three horizontal bars joined by side walls form two stacked enclosed
# regions in a 5x5 crop and exactly 19 cells, matching the official task.
_DOUBLE_19 = (
    {(r, c) for r in (0, 2, 4) for c in range(5)}
    | {(r, c) for r in (1, 3) for c in (0, 4)}
)
_DOUBLE_16 = (
    {(r, c) for r in (0, 2, 4) for c in range(4)}
    | {(r, c) for r in (1, 3) for c in (0, 3)}
)
_TWO_HOLE = (
    _DOUBLE_19,
    _DOUBLE_16,
    _DOUBLE_19 | {(1, 5)},
)


def _normalize(cells: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    cells = set(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return {(r - r0, c - c0) for r, c in cells}


def _transform(cells: set[tuple[int, int]], transform: int) -> set[tuple[int, int]]:
    """Apply one of eight dihedral transforms and normalize."""
    pts = set(cells)
    for _ in range(transform % 4):
        pts = {(c, -r) for r, c in pts}
    if transform >= 4:
        pts = {(r, -c) for r, c in pts}
    return _normalize(pts)


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _shape_dims(cells: set[tuple[int, int]]) -> tuple[int, int]:
    _, _, r2, c2 = _bbox(cells)
    return r2 + 1, c2 + 1


def _components(grid: list[list[int]]) -> list[dict]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            todo = [(r, c)]
            seen.add((r, c))
            cells: set[tuple[int, int]] = set()
            while todo:
                rr, cc = todo.pop()
                cells.add((rr, cc))
                for dr, dc in _DIR4:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            components.append({"color": color, "cells": cells, "bbox": _bbox(cells)})
    return components


def _crop_object(grid: list[list[int]], obj: dict) -> list[list[int]]:
    r1, c1, r2, c2 = obj["bbox"]
    return [row[c1 : c2 + 1] for row in grid[r1 : r2 + 1]]


def _hole_count_cells(cells: set[tuple[int, int]]) -> int:
    norm = _normalize(cells)
    h, w = _shape_dims(norm)
    seen: set[tuple[int, int]] = set()
    holes = 0
    for r in range(h):
        for c in range(w):
            if (r, c) in norm or (r, c) in seen:
                continue
            todo = deque([(r, c)])
            seen.add((r, c))
            touches_edge = False
            while todo:
                rr, cc = todo.popleft()
                if rr in (0, h - 1) or cc in (0, w - 1):
                    touches_edge = True
                for dr, dc in _DIR4:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in norm
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            if not touches_edge:
                holes += 1
    return holes


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    items = []
    for obj in _components(grid):
        holes = _hole_count_cells(obj["cells"])
        r1, c1, _, _ = obj["bbox"]
        items.append((holes, len(obj["cells"]), r1, c1, _rotate_cw(_crop_object(grid, obj))))
    items.sort(key=lambda x: x[:4])
    pieces = [item[4] for item in items]
    out_h = max(len(piece) for piece in pieces)
    out_w = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    out = full_grid(out_h, out_w, 0)
    left = 0
    for piece in pieces:
        top = (out_h - len(piece)) // 2
        for r, row in enumerate(piece):
            for c, value in enumerate(row):
                if value != 0:
                    out[top + r][left + c] = value
        left += len(piece[0]) + 1
    return out


def _analyze(grid: list[list[int]]) -> dict:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be non-empty"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["grid rows must be non-empty"]}
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return {"errors": ["grid must be rectangular"]}
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
        return {"errors": errors}

    components = _components(grid)
    colors = [obj["color"] for obj in components]
    if not 3 <= len(components) <= 5:
        errors.append("scene must contain three through five objects")
    if len(colors) != len(set(colors)):
        errors.append("each nonzero color must identify exactly one object")

    # Different colors must have at least one complete blank cell around them.
    owner = {}
    for i, obj in enumerate(components):
        for cell in obj["cells"]:
            owner[cell] = i
    for (r, c), i in owner.items():
        for dr, dc in _DIR8:
            other = owner.get((r + dr, c + dc))
            if other is not None and other != i:
                errors.append("objects of different colors may not touch, even diagonally")
                break
        if errors and errors[-1].startswith("objects of different"):
            break

    specs = []
    for obj in components:
        holes = _hole_count_cells(obj["cells"])
        if len(obj["cells"]) < 4:
            errors.append("every object must contain at least four cells")
        if holes > 2:
            errors.append("generated/canonical grammar supports at most two holes per object")
        specs.append(
            {
                "holes": holes,
                "size": len(obj["cells"]),
                "top": obj["bbox"][0],
                "left": obj["bbox"][1],
                "bbox": obj["bbox"],
                "color": obj["color"],
                "cells": obj["cells"],
            }
        )
    if specs and not any(spec["holes"] == 0 for spec in specs):
        errors.append("scene must include a hole-free object")
    if specs and not any(spec["holes"] >= 1 for spec in specs):
        errors.append("scene must include an object with an enclosed hole")

    profile = None
    hole_set = {spec["holes"] for spec in specs}
    zero_specs = [spec for spec in specs if spec["holes"] == 0]
    if {0, 1, 2}.issubset(hole_set):
        profile = "hole_primary"
    elif len(zero_specs) >= 2:
        same_size_pairs = [
            (a, b)
            for i, a in enumerate(zero_specs)
            for b in zero_specs[i + 1 :]
            if a["size"] == b["size"]
        ]
        if same_size_pairs:
            if any(a["top"] == b["top"] for a, b in same_size_pairs):
                profile = "col_tiebreak"
            else:
                profile = "row_tiebreak"
        elif len({spec["size"] for spec in zero_specs}) >= 2:
            profile = "size_secondary"
    return {
        "errors": errors,
        "components": components,
        "specs": specs,
        "profile": profile,
        "grid_h": len(grid),
        "grid_w": w,
    }


def observe_overrides(grid: list[list[int]]) -> dict[str, int | str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    if analysis["profile"] not in LESSON_PROFILES:
        raise ValueError("scene does not realize one declared lesson_profile")
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n": len(analysis["components"]),
        "lesson_profile": analysis["profile"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    return list(_analyze(grid)["errors"])


def _profile_specs(profile: str, n: int) -> list[tuple[int, int]]:
    """Return (hole_count, template_index) for each object."""
    if profile == "hole_primary":
        specs = [(0, 0), (1, 0), (2, 0), (0, 2), (1, 2)]
    elif profile == "size_secondary":
        specs = [(0, 0), (0, 4), (1, 0), (1, 2), (1, 4)]
    elif profile in ("row_tiebreak", "col_tiebreak"):
        specs = [(0, 1), (0, 1), (1, 0), (1, 2), (1, 4)]
    else:
        raise ValueError(f"unknown lesson_profile: {profile!r}")
    return specs[:n]


def _template(holes: int, index: int) -> set[tuple[int, int]]:
    family = {0: _ZERO_HOLE, 1: _ONE_HOLE, 2: _TWO_HOLE}[holes]
    return set(family[index % len(family)])


def _can_place(grid: list[list[int]], cells: set[tuple[int, int]], r0: int, c0: int) -> bool:
    h, w = len(grid), len(grid[0])
    translated = {(r0 + r, c0 + c) for r, c in cells}
    if any(not (0 <= r < h and 0 <= c < w) for r, c in translated):
        return False
    for r, c in translated:
        if grid[r][c] != 0:
            return False
        for dr, dc in _DIR8:
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] != 0:
                return False
    return True


def _paint(grid: list[list[int]], cells: set[tuple[int, int]], r0: int, c0: int, color: int) -> None:
    for r, c in cells:
        grid[r0 + r][c0 + c] = color


def _place_random(grid, cells, color, rng) -> bool:
    h, w = len(grid), len(grid[0])
    sh, sw = _shape_dims(cells)
    if sh > h or sw > w:
        return False
    positions = [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]
    rng.shuffle(positions)
    for r0, c0 in positions:
        if _can_place(grid, cells, r0, c0):
            _paint(grid, cells, r0, c0, color)
            return True
    return False


def _build_scene(h: int, w: int, n: int, profile: str, rng) -> list[list[int]]:
    base_specs = _profile_specs(profile, n)
    colors = rng.sample(range(1, 10), n)

    for restart in range(80):
        grid = full_grid(h, w, 0)
        motifs: list[set[tuple[int, int]]] = []
        for i, (holes, template_index) in enumerate(base_specs):
            # The two tie-break objects must remain shape/size identical.
            if profile in ("row_tiebreak", "col_tiebreak") and i == 1:
                motif = set(motifs[0])
            else:
                transform = rng.randrange(8)
                motif = _transform(_template(holes, template_index), transform)
            motifs.append(motif)

        placed = 0
        if profile in ("row_tiebreak", "col_tiebreak"):
            pair = motifs[0]
            sh, sw = _shape_dims(pair)
            if profile == "row_tiebreak":
                max_top = h - (2 * sh + 2)
                if max_top < 0:
                    continue
                r1 = rng.randint(0, max_top)
                r2 = rng.randint(r1 + sh + 2, h - sh)
                c1 = rng.randint(0, w - sw)
                c2 = rng.randint(0, w - sw)
            else:
                max_left = w - (2 * sw + 2)
                if max_left < 0:
                    continue
                c1 = rng.randint(0, max_left)
                c2 = rng.randint(c1 + sw + 2, w - sw)
                r1 = r2 = rng.randint(0, h - sh)
            if not _can_place(grid, pair, r1, c1):
                continue
            _paint(grid, pair, r1, c1, colors[0])
            if not _can_place(grid, pair, r2, c2):
                continue
            _paint(grid, pair, r2, c2, colors[1])
            placed = 2

        ok = True
        for i in range(placed, n):
            if not _place_random(grid, motifs[i], colors[i], rng):
                ok = False
                break
        if ok:
            analysis = _analyze(grid)
            if not analysis["errors"] and analysis["profile"] == profile:
                return grid
    raise ValueError(
        f"could not realize {profile} layout in {h}x{w} after 80 deterministic restarts"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    # The schedule guarantees that every four-example lesson demonstrates all
    # four lexicographic branches.  A caller-provided exact override wins.
    effective_overrides = dict(overrides)
    effective_overrides.setdefault(
        "lesson_profile", LESSON_PROFILES[sample_index % len(LESSON_PROFILES)]
    )
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    h = ctx.draw_int_diff("grid_h", 14, 20)
    w = ctx.draw_int_diff("grid_w", 16, 24)
    n = ctx.draw_int_diff("n", 3, 5)
    profile = ctx.draw_choice("lesson_profile", LESSON_PROFILES)
    return _build_scene(h, w, n, profile, ctx.draw_rng("layout"))
