"""Input generator for ARC task 4290ef0e / library id 5a01897eb8be.

The pinned rule measures, for each non-background color, its bounding-box
maximum dimension and the longest monochrome corner-arm.  Those measurements
assign colors to concentric odd-sized rings; each output ring is drawn as four
corner Ls using that color's measured arm length.

This sampler deliberately varies the evidence needed to infer both clauses:
shape-size order is independent of row-major appearance order, and partial
corner arms prevent a solid-border shortcut.  Outputs remain label-authority
work and are never sampled here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5a01897eb8be"
TASK_ID = GENERATOR_ID
RULE_HASH = "00935b1c1bf9"
VERSION = "3.0.0"
SUMMARY = (
    "A 13..24 by 17..24 grid has an arbitrary top-left background and 3..6 "
    "colored corner glyphs.  A glyph's bounding-box maximum dimension assigns "
    "it to the smallest available odd ring that fits (loose fits before exact "
    "fits, then exact fits largest-first); its longest corner arm controls how "
    "much of each output-ring corner is colored.  Shape placement is randomized "
    "so row-major appearance does not reveal ring order."
)

INVARIANTS = [
    "the top-left cell is the background, which may be any ARC color",
    "there are 3..6 distinct non-background colors",
    "each color has a measurable corner glyph and fits one unique output ring",
    "row-major first appearance disagrees with outer-to-inner ring order",
    "at least one assigned ring has a genuinely partial corner arm",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 13..20", "valid": "13..24"},
    "grid_w": {"type": "int", "default": "scheduled 17..22", "valid": "17..24"},
    "shape_count": {"type": "int", "default": "scheduled 3..6", "valid": "3..6"},
    "has_center": {"type": "bool", "default": "scheduled", "valid": "true|false"},
    "background": {"type": "int", "default": "scheduled ARC color", "valid": "0..9"},
    "loose_shape": {"type": "bool", "default": "scheduled", "valid": "true|false"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# The first four rows are the four canonical (height, width, palette-size)
# profiles, without replaying any canonical placement, color assignment, or
# glyph.  Two broad rows keep dimensions and branches from collapsing to those
# anchors.  The same cycle is used in every difficulty band so all override
# domains and semantic branches remain visible everywhere.
_PROFILE_ROWS = (
    ("center_4", 18, 18, 4, True, 8, False),
    ("no_center_3", 13, 17, 3, False, 4, False),
    ("center_6", 18, 18, 6, True, 3, False),
    ("loose_5", 19, 19, 5, False, 1, True),
    ("center_loose_4", 20, 21, 4, True, 0, True),
    ("broad_no_center_5", 17, 22, 5, False, 9, False),
)
_PROFILE_BY_NAME = {row[0]: row for row in _PROFILE_ROWS}
SCHEDULE_PROFILES = tuple(row[0] for row in _PROFILE_ROWS)
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 3


@dataclass(frozen=True)
class _Glyph:
    color: int
    max_dim: int
    height: int
    width: int
    arm: int
    cells: tuple[tuple[int, int], ...]


def _strict_int(value: Any, name: str, *, nonnegative: bool = False) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
    if nonnegative and value < 0:
        raise ValueError(f"{name} must be nonnegative")
    return value


def _band(difficulty: Any) -> str | None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            f"unknown difficulty {difficulty!r}; expected easy, medium, hard, or None"
        )
    return difficulty


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic curriculum slot; seed and band do not hide slots."""
    del seed
    _band(difficulty)
    _strict_int(sample_index, "sample_index", nonnegative=True)
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _draw_scheduled_int(ctx, name: str, low: int, high: int, scheduled: int) -> int:
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, low, high)
    return ctx.draw_choice(name, (scheduled,))


def _draw_scheduled_bool(ctx, name: str, scheduled: bool) -> bool:
    if ctx.overrides.get(name) is not None:
        value = ctx.overrides[name]
        if type(value) is not bool:
            raise TypeError(f"{name} must be a bool, not {type(value).__name__}")
        return ctx.draw_choice(name, (False, True))
    return ctx.draw_choice(name, (scheduled,))


def _draw_scheduled_color(ctx, name: str, scheduled: int) -> int:
    if ctx.overrides.get(name) is not None:
        return ctx.draw_color_strict(name)
    return ctx.draw_choice(name, (scheduled,))


def _ring_sizes(shape_count: int, has_center: bool) -> list[int]:
    start = 1 if has_center else 3
    return [start + 2 * index for index in range(shape_count)]


def _shape_sizes(shape_count: int, has_center: bool, loose_shape: bool, rng) -> list[int]:
    rings = _ring_sizes(shape_count, has_center)
    if not loose_shape:
        return list(rings)
    # Leave the largest exact ring absent.  A single even-sized loose glyph
    # claims an interior ring first; descending exact fits then shift outward
    # into the deliberately free largest ring, exactly as the authority does.
    first_target = 1 if has_center else 0
    target_index = rng.choice(list(range(first_target, shape_count - 1)))
    return list(rings[:-1]) + [rings[target_index] - 1]


def _corner_cells(
    height: int, width: int, arm: int, corners: Iterable[str]
) -> tuple[tuple[int, int], ...]:
    cells: set[tuple[int, int]] = set()
    for corner in corners:
        if corner == "tl":
            cells.update((0, step) for step in range(arm))
            cells.update((step, 0) for step in range(arm))
        elif corner == "tr":
            cells.update((0, width - 1 - step) for step in range(arm))
            cells.update((step, width - 1) for step in range(arm))
        elif corner == "bl":
            cells.update((height - 1, step) for step in range(arm))
            cells.update((height - 1 - step, 0) for step in range(arm))
        elif corner == "br":
            cells.update((height - 1, width - 1 - step) for step in range(arm))
            cells.update((height - 1 - step, width - 1) for step in range(arm))
        else:  # pragma: no cover - private construction invariant
            raise ValueError(f"unknown corner {corner!r}")
    return tuple(sorted(cells))


def _build_glyphs(
    sizes: list[int], colors: tuple[int, ...], ctx, difficulty: str | None
) -> list[_Glyph]:
    # Difficulty is intentionally part of the keyed geometry stream: bands keep
    # the same lawful axis support, but do not collapse to byte-identical grids.
    band_tag = difficulty or "default"
    rng = ctx.draw_rng(f"glyph_geometry_{band_tag}")
    non_singletons = [index for index, size in enumerate(sizes) if size > 1]
    # A size-5 connected L has nine cells, matching the canonical task's
    # largest-component scale (median 8) while leaving other glyphs fragmented.
    connected_index = min(
        non_singletons, key=lambda index: (abs(sizes[index] - 5), sizes[index])
    )
    glyphs: list[_Glyph] = []
    for index, (size, color) in enumerate(zip(sizes, colors)):
        if size == 1:
            glyphs.append(_Glyph(color, 1, 1, 1, 1, ((0, 0),)))
            continue
        if index == connected_index:
            cells = _corner_cells(size, size, size, ("tl",))
            glyphs.append(_Glyph(color, size, size, size, size, cells))
            continue

        dimensions = [(size, size)]
        if size > 2:
            dimensions.extend(((size, size - 1), (size - 1, size)))
        height, width = rng.choice(dimensions)
        max_arm = max(1, min(3, (min(height, width) - 1) // 2))
        arm = rng.randint(1, max_arm)
        # Four-corner glyphs occur at a stable cadence; the rest use two
        # diagonal components.  Both span the intended full bounding box.
        corners = ("tl", "tr", "bl", "br") if index % 3 == 1 else ("tl", "br")
        cells = _corner_cells(height, width, arm, corners)
        glyphs.append(_Glyph(color, size, height, width, arm, cells))
    return glyphs


def _absolute_cells(glyph: _Glyph, top: int, left: int) -> tuple[tuple[int, int], ...]:
    return tuple((top + row, left + col) for row, col in glyph.cells)


def _first_appearance(grid: list[list[int]]) -> list[int]:
    background = grid[0][0]
    seen: set[int] = set()
    order: list[int] = []
    for row in grid:
        for value in row:
            if value != background and value not in seen:
                seen.add(value)
                order.append(value)
    return order


def _planned_assignments(glyphs: list[_Glyph], has_center: bool):
    rings = _ring_sizes(len(glyphs), has_center)
    available = list(rings)
    exact = [glyph for glyph in glyphs if glyph.max_dim in rings]
    loose = [glyph for glyph in glyphs if glyph.max_dim not in rings]
    assignments: list[tuple[_Glyph, int]] = []
    for glyph in loose + sorted(exact, key=lambda item: -item.max_dim):
        target = next((ring for ring in available if ring >= glyph.max_dim), None)
        if target is None:  # pragma: no cover - constructor is exhaustive-tested
            raise RuntimeError(f"glyph max-dim {glyph.max_dim} fits no ring")
        available.remove(target)
        assignments.append((glyph, target))
    return assignments


def _place_glyphs(
    height: int,
    width: int,
    background: int,
    glyphs: list[_Glyph],
    has_center: bool,
    rng,
) -> list[list[int]]:
    planned_outer = [
        glyph.color
        for glyph, _ in sorted(
            _planned_assignments(glyphs, has_center), key=lambda item: -item[1]
        )
    ]
    # Place denser glyphs first for constructive feasibility. Candidate positions
    # are independently shuffled, so this search order does not leak ring order.
    order = sorted(
        range(len(glyphs)),
        key=lambda index: (-len(glyphs[index].cells), -glyphs[index].height * glyphs[index].width),
    )

    for _attempt in range(48):
        occupied: set[tuple[int, int]] = set()
        placements: dict[int, tuple[int, int]] = {}

        def search(depth: int) -> bool:
            if depth == len(order):
                return True
            index = order[depth]
            glyph = glyphs[index]
            candidates = [
                (row, col)
                for row in range(height - glyph.height + 1)
                for col in range(width - glyph.width + 1)
            ]
            rng.shuffle(candidates)
            for top, left in candidates:
                cells = _absolute_cells(glyph, top, left)
                if (0, 0) in cells or any(cell in occupied for cell in cells):
                    continue
                placements[index] = (top, left)
                occupied.update(cells)
                if search(depth + 1):
                    return True
                occupied.difference_update(cells)
                placements.pop(index, None)
            return False

        if not search(0):
            continue
        grid = full_grid(height, width, background)
        for index, glyph in enumerate(glyphs):
            top, left = placements[index]
            for row, col in _absolute_cells(glyph, top, left):
                grid[row][col] = glyph.color
        if _first_appearance(grid) != planned_outer:
            return grid
    raise RuntimeError("constructive placement could not break scan-order shortcut")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _strict_int(seed, "seed")
    _strict_int(sample_index, "sample_index", nonnegative=True)
    _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axes: " + ", ".join(unknown))

    profile_name = schedule_profile(seed, sample_index, difficulty)
    _, ph, pw, pn, pc, pbg, ploose = _PROFILE_BY_NAME[profile_name]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_scheduled_int(ctx, "grid_h", 13, 24, ph)
    width = _draw_scheduled_int(ctx, "grid_w", 17, 24, pw)
    shape_count = _draw_scheduled_int(ctx, "shape_count", 3, 6, pn)
    has_center = _draw_scheduled_bool(ctx, "has_center", pc)
    background = _draw_scheduled_color(ctx, "background", pbg)
    loose_shape = _draw_scheduled_bool(ctx, "loose_shape", ploose)

    sizes = _shape_sizes(
        shape_count, has_center, loose_shape, ctx.draw_rng("shape_size_assignment")
    )
    colors = ctx.draw_distinct_colors("glyph_colors", n=shape_count, exclude=(background,))
    glyphs = _build_glyphs(sizes, colors, ctx, difficulty)
    grid = _place_glyphs(
        height,
        width,
        background,
        glyphs,
        has_center,
        ctx.draw_rng(f"layout_{difficulty or 'default'}"),
    )
    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:  # pragma: no cover - defensive guard around constructive code
        raise RuntimeError("constructed invalid grid: " + "; ".join(errors))
    return grid


# ---- Independent analysis of returned pixels -----------------------------


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    height = len(grid)
    errors: list[str] = []
    if height > 30 or width > 30:
        errors.append(f"grid dimensions exceed ARC limit: {height}x{width}")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be literal integer ARC colors 0..9")
    return errors


def _count_extent(grid, color: int, row: int, col: int, dr: int, dc: int) -> int:
    height, width = len(grid), len(grid[0])
    length = 0
    while 0 <= row < height and 0 <= col < width and grid[row][col] == color:
        length += 1
        row += dr
        col += dc
    return length


def _color_info(grid, color: int) -> dict[str, Any]:
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    bbox = (min(rows), min(cols), max(rows), max(cols))
    max_dim = max(bbox[2] - bbox[0] + 1, bbox[3] - bbox[1] + 1)
    arm = 0
    for row, col in cells:
        for dr in (-1, 1):
            for dc in (-1, 1):
                arm = max(
                    arm,
                    min(
                        _count_extent(grid, color, row, col, 0, dc),
                        _count_extent(grid, color, row, col, dr, 0),
                    ),
                )
    return {"color": color, "cells": cells, "bbox": bbox, "max_dim": max_dim, "arm": arm}


def _analyze(grid) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    background = grid[0][0]
    colors = sorted({value for row in grid for value in row if value != background})
    infos = [_color_info(grid, color) for color in colors]
    has_center = any(info["max_dim"] == 1 for info in infos)
    rings = _ring_sizes(len(infos), has_center)
    available = list(rings)
    exact = [info for info in infos if info["max_dim"] in rings]
    loose = [info for info in infos if info["max_dim"] not in rings]
    assignments: list[tuple[dict[str, Any], int]] = []
    for info in loose + sorted(exact, key=lambda item: -item["max_dim"]):
        target = next((ring for ring in available if ring >= info["max_dim"]), None)
        if target is None:
            raise ValueError(
                f"color {info['color']} max-dim {info['max_dim']} fits no remaining ring"
            )
        available.remove(target)
        assignments.append((info, target))
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "background": background,
        "infos": infos,
        "shape_count": len(infos),
        "has_center": has_center,
        "loose_shape": bool(loose),
        "rings": rings,
        "assignments": assignments,
    }


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every declared axis from pixels rather than draw bookkeeping."""
    details = _analyze(grid)
    return {
        "grid_h": details["height"],
        "grid_w": details["width"],
        "shape_count": details["shape_count"],
        "has_center": details["has_center"],
        "background": details["background"],
        "loose_shape": details["loose_shape"],
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    errors = _grid_errors(grid)
    if errors:
        return errors
    background = grid[0][0]
    colors = sorted({value for row in grid for value in row if value != background})
    if not 3 <= len(colors) <= 6:
        errors.append(f"expected 3..6 non-background colors, found {len(colors)}")
        return errors
    try:
        details = _analyze(grid)
    except ValueError as exc:
        errors.append(str(exc))
        return errors
    if len(details["assignments"]) != len(colors):
        errors.append("not every color was assigned exactly one ring")
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and requested is not None:
            actual = observe_overrides(grid).get(name)
            if actual != requested:
                errors.append(f"override {name}={requested!r} realized as {actual!r}")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


# ---- Semantic rivals and lesson contract ---------------------------------


def _l_cells(arm: int, size: int) -> set[tuple[int, int]]:
    top_left = {(0, step) for step in range(arm)} | {(step, 0) for step in range(arm)}
    result: set[tuple[int, int]] = set()
    for row, col in top_left:
        result.update(
            {
                (row, col),
                (row, size - 1 - col),
                (size - 1 - row, col),
                (size - 1 - row, size - 1 - col),
            }
        )
    return result


def _render(details, assignments, *, solid: bool = False):
    size = max(details["rings"])
    middle = size // 2
    output = full_grid(size, size, details["background"])
    for info, ring_size in sorted(assignments, key=lambda item: -item[1]):
        arm = ring_size if solid else min(info["arm"], ring_size)
        offset = middle - ring_size // 2
        for row, col in _l_cells(arm, ring_size):
            output[offset + row][offset + col] = info["color"]
    return output


def _canonical_output(grid):
    details = _analyze(grid)
    return _render(details, details["assignments"])


def _scan_order_rival(grid):
    details = _analyze(grid)
    by_color = {info["color"]: info for info in details["infos"]}
    assignments = list(
        zip(
            (by_color[color] for color in _first_appearance(grid)),
            reversed(details["rings"]),
        )
    )
    return _render(details, assignments)


def _solid_rings_rival(grid):
    details = _analyze(grid)
    return _render(details, details["assignments"], solid=True)


def _scan_order_break(grid) -> bool:
    details = _analyze(grid)
    intended = [
        info["color"]
        for info, _ in sorted(details["assignments"], key=lambda item: -item[1])
    ]
    return _first_appearance(grid) != intended


def _partial_arms(grid) -> bool:
    details = _analyze(grid)
    return any(info["arm"] < ring for info, ring in details["assignments"])


def _has_center_witness(grid) -> bool:
    return _analyze(grid)["has_center"]


def _no_center_witness(grid) -> bool:
    return not _analyze(grid)["has_center"]


def _loose_fit_witness(grid) -> bool:
    return _analyze(grid)["loose_shape"]


SEMANTIC_WITNESSES = {
    "scan_order_break": _scan_order_break,
    "partial_arms": _partial_arms,
    "has_center": _has_center_witness,
    "no_center": _no_center_witness,
    "loose_fit": _loose_fit_witness,
}
BRANCH_WITNESSES = ("has_center", "no_center", "loose_fit")
SEMANTIC_RIVALS = {
    "scan_order": _scan_order_rival,
    "solid_rings": _solid_rings_rival,
}
WITNESS_RIVALS = {
    "scan_order_break": ("scan_order",),
    "partial_arms": ("solid_rings",),
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson only when a declared wrong rule survives its demos."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
