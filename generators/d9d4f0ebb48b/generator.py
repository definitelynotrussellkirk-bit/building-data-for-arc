"""Generator for task ``d9d4f0ebb48b`` — grow monochrome pluses.

Every interior cell whose four cardinal neighbours have the same nonzero color
is the center of a plus.  Fill that center's complete 3x3 neighbourhood with
its color.  All other cells are preserved.

The four-sample curriculum keeps a clean canonical-like scene and adds three
controlled counterexamples: a five-cell monochrome L whose bounding box must *not* be
filled, a multicolor cross whose occupied arms must *not* trigger, and two
same-color pluses including a border-touching footprint.  These distinguish the
true local predicate from component-bbox, color-blind-cross, one-per-color, and
interior-only shortcuts. Nonzero colors never reserve semantic roles: every
color can trigger, and each distractor shares a color with a true plus.
"""
from __future__ import annotations

import copy
from collections import deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d9d4f0ebb48b"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "e629f64db51d"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "A zero-background grid contains one or two separated same-color pluses. "
    "For every nonzero center whose north, south, west, and east neighbours "
    "all equal the center, fill its entire 3x3 neighbourhood with that color. "
    "Preserve every other cell. A four-profile schedule includes clean "
    "canonical anchors, an unchanged five-cell monochrome L distractor, an unchanged "
    "multicolor false cross, and repeated-color pluses with a border-touching "
    "footprint. All nonzero colors may trigger; distractors reuse true-plus "
    "colors so neither absolute palette IDs nor per-color filtering solve it."
)

INVARIANTS = [
    "background is color 0",
    "there are one or two non-overlapping monochrome five-cell plus triggers",
    "the four diagonal cells of every trigger footprint are initially zero",
    "optional distractors are structurally distinct from a monochrome plus",
    "colors 1..9 can all trigger; generated distractors share a true-plus color",
    "the output preserves all input cells and fills exactly the 3x3 footprint of every trigger",
]

SCENE_PROFILES = (
    "clean",
    "l_distractor",
    "multicolor_cross",
    "boundary_repeat",
)
SCHEDULE_PROFILES = SCENE_PROFILES
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES = ("no_pluses", "already_filled", "missing_arm")
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "profile-keyed canonical anchors and 7..14 generalized sizes",
        "valid": "7..14",
        "doc": "input grid height",
    },
    "grid_w": {
        "type": "int",
        "default": "profile-keyed canonical anchors and 8..14 generalized sizes",
        "valid": "8..14",
        "doc": "input grid width",
    },
    "plus_count": {
        "type": "int",
        "default": "1 for the easy clean anchor; otherwise 2",
        "valid": "1..2",
        "doc": "number of true monochrome plus centers",
    },
    "scene_profile": {
        "type": "str",
        "default": "four-sample cyclic curriculum",
        "valid": "|".join(SCENE_PROFILES),
        "doc": "observable distractor/boundary profile",
    },
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_PLUS_OFFSETS = ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))
_PLUS_COLORS = tuple(range(1, 10))


def _normalize_band(difficulty: Any) -> str:
    if difficulty in (None, "default", "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the deterministic profile used by the sliding lesson schedule."""
    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def _scheduled_int(ctx, overrides: dict[str, Any], label: str,
                   default: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return int(ctx.draw_int(label, lo, hi))
    return int(ctx.draw_int(label, default, default))


def _scheduled_choice(ctx, overrides: dict[str, Any], label: str,
                      default: str, options: tuple[str, ...]) -> str:
    if label in overrides and overrides[label] is not None:
        return str(ctx.draw_choice(label, options))
    return str(ctx.draw_choice(label, (default,)))


def _profile_defaults(profile: str, band: str) -> tuple[int, int, int]:
    """Return height, width, plus_count for the ordinary scheduled draw."""
    if profile == "clean":
        # Exact canonical (height, width, palette-size) anchors in every band.
        return {
            "easy": (8, 8, 1),       # canonical train: one color-6 plus
            "medium": (7, 9, 2),     # canonical train: colors 2 and 4
            "hard": (9, 10, 2),      # canonical train: colors 3 and 7
        }[band]
    if profile == "l_distractor":
        return {
            "easy": (7, 8, 2),
            "medium": (9, 11, 2),
            "hard": (12, 14, 2),
        }[band]
    if profile == "multicolor_cross":
        return {
            "easy": (8, 9, 2),
            "medium": (10, 12, 2),
            "hard": (14, 14, 2),
        }[band]
    if profile == "boundary_repeat":
        return {
            "easy": (7, 9, 2),
            "medium": (8, 11, 2),    # canonical test scale
            "hard": (13, 13, 2),
        }[band]
    raise ValueError(f"unknown scene profile: {profile!r}")


def _rect_separated(a: tuple[int, int, int, int],
                    b: tuple[int, int, int, int], gap: int = 1) -> bool:
    ar0, ac0, ar1, ac1 = a
    br0, bc0, br1, bc1 = b
    return (
        ar1 + gap < br0
        or br1 + gap < ar0
        or ac1 + gap < bc0
        or bc1 + gap < ac0
    )


def _touches_border(rect: tuple[int, int, int, int], h: int, w: int) -> bool:
    r0, c0, r1, c1 = rect
    return r0 == 0 or c0 == 0 or r1 == h - 1 or c1 == w - 1


def _pack_footprints(h: int, w: int, count: int, rng,
                     *, first_must_touch_border: bool = False
                     ) -> list[tuple[int, int, int, int]]:
    """Pack separated 3x3 footprints, using deterministic backtracking."""
    candidates = [
        (r, c, r + 2, c + 2)
        for r in range(h - 2)
        for c in range(w - 2)
    ]
    rng.shuffle(candidates)
    if first_must_touch_border:
        candidates.sort(key=lambda rect: not _touches_border(rect, h, w))

    chosen: list[tuple[int, int, int, int]] = []

    def visit(start: int) -> bool:
        if len(chosen) == count:
            return True
        for index in range(start, len(candidates)):
            rect = candidates[index]
            if not chosen and first_must_touch_border and not _touches_border(rect, h, w):
                continue
            if all(_rect_separated(rect, other) for other in chosen):
                chosen.append(rect)
                if visit(index + 1):
                    return True
                chosen.pop()
        return False

    if not visit(0):
        raise ValueError(
            f"incompatible footprint request: cannot place {count} separated "
            f"3x3 regions in {h}x{w}"
        )
    return chosen


def _paint_plus(grid: list[list[int]], rect: tuple[int, int, int, int],
                color: int) -> tuple[int, int]:
    r0, c0, _r1, _c1 = rect
    center = (r0 + 1, c0 + 1)
    for dr, dc in _PLUS_OFFSETS:
        grid[center[0] + dr][center[1] + dc] = color
    return center


def _clean_colors(band: str, count: int) -> tuple[int, ...]:
    preferred = {
        "easy": (6, 4),
        "medium": (2, 4),
        "hard": (3, 7),
    }[band]
    return preferred[:count]


def _plus_colors(profile: str, band: str, count: int, rng) -> tuple[int, ...]:
    # Keep canonical palettes on one third of clean draws, while allowing
    # every nonzero color in every profile. The zero background stays fixed.
    if profile == "clean" and rng.randrange(3) == 0:
        return _clean_colors(band, count)
    if profile == "boundary_repeat":
        color = rng.choice(_PLUS_COLORS)
        return tuple(color for _ in range(count))
    colors = list(_PLUS_COLORS)
    rng.shuffle(colors)
    return tuple(colors[:count])


def _paint_l_distractor(grid: list[list[int]], rect, rng, color: int) -> None:
    r0, c0, _r1, _c1 = rect
    # Match the plus's area as well as its color. A three-cell L still lets
    # "fill every five-cell component bbox" solve the entire curriculum.
    corner = rng.randrange(4)
    edge_row = r0 + (2 if corner & 2 else 0)
    edge_col = c0 + (2 if corner & 1 else 0)
    for offset in range(3):
        grid[edge_row][c0 + offset] = color
        grid[r0 + offset][edge_col] = color


def _paint_multicolor_cross(grid: list[list[int]], rect,
                            center_color: int, arm_color: int) -> None:
    r0, c0, _r1, _c1 = rect
    center = (r0 + 1, c0 + 1)
    grid[center[0]][center[1]] = center_color
    for dr, dc in _CARDINAL:
        grid[center[0] + dr][center[1] + dc] = arm_color


def _paint_boundary_bar(grid: list[list[int]], rect, rng, color: int) -> None:
    r0, c0, _r1, _c1 = rect
    if rng.choice((False, True)):
        for dc in range(3):
            grid[r0 + 1][c0 + dc] = color
    else:
        for dr in range(3):
            grid[r0 + dr][c0 + 1] = color


def generate(seed: int, sample_index: int, *, difficulty: Any = None,
             **overrides: Any) -> list[list[int]]:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    band = _normalize_band(difficulty)
    scheduled_profile = schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = _scheduled_choice(
        ctx, overrides, "scene_profile", scheduled_profile, SCENE_PROFILES
    )
    # If scene_profile is overridden, use that profile's lawful ordinary
    # defaults for every non-overridden dependent axis.
    h0, w0, n0 = _profile_defaults(profile, band)
    height = _scheduled_int(ctx, overrides, "grid_h", h0, 7, 14)
    width = _scheduled_int(ctx, overrides, "grid_w", w0, 8, 14)
    plus_count = _scheduled_int(ctx, overrides, "plus_count", n0, 1, 2)

    rng = ctx.draw_rng("layout")
    distractor_count = 0 if profile == "clean" else 1
    footprints = _pack_footprints(
        height,
        width,
        plus_count + distractor_count,
        rng,
        first_must_touch_border=(profile == "boundary_repeat"),
    )
    grid = full_grid(height, width, 0)
    palette_rng = ctx.draw_rng("palette")
    colors = _plus_colors(profile, band, plus_count, palette_rng)
    for rect, color in zip(footprints[:plus_count], colors):
        _paint_plus(grid, rect, color)

    if distractor_count:
        distractor_rect = footprints[-1]
        if profile == "l_distractor":
            _paint_l_distractor(grid, distractor_rect, rng, palette_rng.choice(colors))
        elif profile == "multicolor_cross":
            center_color = palette_rng.choice(colors)
            arm_color = palette_rng.choice(tuple(c for c in _PLUS_COLORS if c != center_color))
            _paint_multicolor_cross(grid, distractor_rect, center_color, arm_color)
        elif profile == "boundary_repeat":
            _paint_boundary_bar(grid, distractor_rect, rng, colors[0])
        else:  # defensive; profile was validated by draw_choice
            raise ValueError(f"unknown scene profile: {profile!r}")

    findings = self_check(grid, difficulty=band)
    if findings:
        raise RuntimeError("generated invalid scene: " + "; ".join(findings))
    return grid


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    errors: list[str] = []
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("cells must be literal ARC integers 0..9")
                return errors
    return errors


def _trigger_centers(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    triggers: list[dict[str, Any]] = []
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            color = grid[row][col]
            if color == 0:
                continue
            if all(grid[row + dr][col + dc] == color for dr, dc in _CARDINAL):
                plus_cells = {
                    (row + dr, col + dc) for dr, dc in _PLUS_OFFSETS
                }
                footprint = {
                    (rr, cc)
                    for rr in range(row - 1, row + 2)
                    for cc in range(col - 1, col + 2)
                }
                triggers.append({
                    "center": (row, col),
                    "color": color,
                    "plus_cells": plus_cells,
                    "footprint": footprint,
                    "touches_border": (
                        row == 1 or col == 1
                        or row == height - 2 or col == width - 2
                    ),
                })
    return triggers


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [row for row, _col in cells]
    cols = [col for _row, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _is_l_distractor(grid: list[list[int]], cells: set[tuple[int, int]]) -> bool:
    colors = {grid[r][c] for r, c in cells}
    if len(cells) not in (3, 5) or len(colors) != 1 or 0 in colors:
        return False
    r0, c0, r1, c1 = _bbox(cells)
    side = (len(cells) + 1) // 2
    if r1 - r0 != side - 1 or c1 - c0 != side - 1:
        return False
    # Accept legacy 2x2 Ls too, but generate 3x3 Ls with plus-matched area.
    return any(
        cells == ({(rr, edge_col) for rr in range(r0, r1 + 1)}
                  | {(edge_row, cc) for cc in range(c0, c1 + 1)})
        for edge_row in (r0, r1) for edge_col in (c0, c1)
    )


def _is_multicolor_cross(grid: list[list[int]], cells: set[tuple[int, int]]) -> bool:
    if len(cells) != 5:
        return False
    r0, c0, r1, c1 = _bbox(cells)
    if r1 - r0 != 2 or c1 - c0 != 2:
        return False
    center = (r0 + 1, c0 + 1)
    expected = {center} | {
        (center[0] + dr, center[1] + dc) for dr, dc in _CARDINAL
    }
    return (
        cells == expected
        and grid[center[0]][center[1]] != 0
        and grid[center[0] - 1][center[1]] not in (0, grid[center[0]][center[1]])
        and all(grid[center[0] + dr][center[1] + dc]
                == grid[center[0] - 1][center[1]] for dr, dc in _CARDINAL)
    )


def _is_boundary_bar(grid: list[list[int]], cells: set[tuple[int, int]]) -> bool:
    colors = {grid[r][c] for r, c in cells}
    if len(cells) != 3 or len(colors) != 1 or 0 in colors:
        return False
    rows = sorted({r for r, _c in cells})
    cols = sorted({c for _r, c in cells})
    return (
        (len(rows) == 1 and len(cols) == 3 and cols[-1] - cols[0] == 2)
        or (len(cols) == 1 and len(rows) == 3 and rows[-1] - rows[0] == 2)
    )


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors, "triggers": [], "scene_profile": None}
    height, width = len(grid), len(grid[0])
    if not 7 <= height <= 14:
        errors.append(f"height must be in 7..14, found {height}")
    if not 8 <= width <= 14:
        errors.append(f"width must be in 8..14, found {width}")

    triggers = _trigger_centers(grid)
    if not 1 <= len(triggers) <= 2:
        errors.append(f"expected 1-2 monochrome plus triggers, found {len(triggers)}")

    occupied_footprints: set[tuple[int, int]] = set()
    plus_cells: set[tuple[int, int]] = set()
    for index, trigger in enumerate(triggers):
        overlap = occupied_footprints & trigger["footprint"]
        if overlap:
            errors.append(f"trigger footprint {index} overlaps another trigger")
        occupied_footprints |= trigger["footprint"]
        plus_cells |= trigger["plus_cells"]
        diagonals = trigger["footprint"] - trigger["plus_cells"]
        filled = sorted((r, c) for r, c in diagonals if grid[r][c] != 0)
        if filled:
            errors.append(
                f"trigger at {trigger['center']} has pre-filled diagonal(s): {filled}"
            )

    nonzero = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    remainder = nonzero - plus_cells
    profile: str | None = None
    if not remainder:
        profile = "clean"
    elif _is_l_distractor(grid, remainder):
        profile = "l_distractor"
    elif _is_multicolor_cross(grid, remainder):
        profile = "multicolor_cross"
    elif _is_boundary_bar(grid, remainder):
        profile = "boundary_repeat"
        if triggers and not any(t["touches_border"] for t in triggers):
            errors.append("boundary_repeat requires a border-touching plus footprint")
        if len(triggers) == 2 and triggers[0]["color"] != triggers[1]["color"]:
            errors.append("boundary_repeat with two pluses requires repeated color")
    else:
        errors.append(
            "non-trigger cells must be absent or exactly one allowed L, "
            "multicolor cross, or length-3 bar distractor"
        )

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "triggers": triggers,
        "plus_count": len(triggers),
        "remainder": remainder,
        "scene_profile": profile,
    }


def observe_overrides(grid: Any) -> dict[str, Any]:
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["scene_profile"] is None:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "plus_count": analysis["plus_count"],
        "scene_profile": analysis["scene_profile"],
    }


def self_check(grid: Any, *, difficulty: Any = None,
               meta: dict[str, Any] | None = None) -> list[str]:
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if meta and isinstance(meta.get("overrides"), dict):
        observed = observe_overrides(grid)
        for key, expected in meta["overrides"].items():
            if key in AXES and expected is not None and observed.get(key) != expected:
                errors.append(
                    f"override {key}={expected!r} not observable; saw {observed.get(key)!r}"
                )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if analysis["scene_profile"] != "clean":
        errors.append("canonical-like scenes contain only separated monochrome pluses")
    colors = [trigger["color"] for trigger in analysis["triggers"]]
    if len(colors) != len(set(colors)):
        errors.append("canonical-like multi-plus scenes use distinct colors")
    return errors


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Faithful Python mirror used only for testing and semantic probes."""
    out = copy.deepcopy(grid)
    height, width = len(grid), len(grid[0])
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            color = grid[row][col]
            if color != 0 and all(
                grid[row + dr][col + dc] == color for dr, dc in _CARDINAL
            ):
                for rr in range(row - 1, row + 2):
                    for cc in range(col - 1, col + 2):
                        out[rr][cc] = color
    return out


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: set[tuple[int, int]] = set()
            while queue:
                r, c = queue.popleft()
                cells.add((r, c))
                for dr, dc in _CARDINAL:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height and 0 <= nc < width
                        and (nr, nc) not in seen and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append({"color": color, "cells": cells})
    return result


def _rival_identity(grid: list[list[int]]) -> list[list[int]]:
    return copy.deepcopy(grid)


def _rival_component_bboxes(grid: list[list[int]]) -> list[list[int]]:
    out = copy.deepcopy(grid)
    for component in _components(grid):
        r0, c0, r1, c1 = _bbox(component["cells"])
        for row in range(r0, r1 + 1):
            for col in range(c0, c1 + 1):
                out[row][col] = component["color"]
    return out


def _rival_palette_gated_bboxes(grid: list[list[int]]) -> list[list[int]]:
    """Old palette shortcut: fill component bboxes only for colors 1..7."""
    out = copy.deepcopy(grid)
    for component in _components(grid):
        if component["color"] not in range(1, 8):
            continue
        r0, c0, r1, c1 = _bbox(component["cells"])
        for row in range(r0, r1 + 1):
            for col in range(c0, c1 + 1):
                out[row][col] = component["color"]
    return out


def _rival_five_cell_bboxes(grid: list[list[int]]) -> list[list[int]]:
    """Shape-blind rival: fill every monochrome five-cell component bbox."""
    out = copy.deepcopy(grid)
    for component in _components(grid):
        if len(component["cells"]) != 5:
            continue
        r0, c0, r1, c1 = _bbox(component["cells"])
        for row in range(r0, r1 + 1):
            for col in range(c0, c1 + 1):
                out[row][col] = component["color"]
    return out


def _rival_color_blind_cross(grid: list[list[int]]) -> list[list[int]]:
    out = copy.deepcopy(grid)
    height, width = len(grid), len(grid[0])
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] != 0 and all(
                grid[row + dr][col + dc] != 0 for dr, dc in _CARDINAL
            ):
                for rr in range(row - 1, row + 2):
                    for cc in range(col - 1, col + 2):
                        out[rr][cc] = grid[row][col]
    return out


def _rival_one_per_color(grid: list[list[int]]) -> list[list[int]]:
    out = copy.deepcopy(grid)
    seen_colors: set[int] = set()
    for trigger in _trigger_centers(grid):
        color = trigger["color"]
        if color in seen_colors:
            continue
        seen_colors.add(color)
        for row, col in trigger["footprint"]:
            out[row][col] = color
    return out


def _rival_skip_boundary(grid: list[list[int]]) -> list[list[int]]:
    out = copy.deepcopy(grid)
    for trigger in _trigger_centers(grid):
        if trigger["touches_border"]:
            continue
        for row, col in trigger["footprint"]:
            out[row][col] = trigger["color"]
    return out


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _rival_identity,
    "component_bbox": _rival_component_bboxes,
    "palette_gated_bbox": _rival_palette_gated_bboxes,
    "five_cell_bbox": _rival_five_cell_bboxes,
    "color_blind_cross": _rival_color_blind_cross,
    "one_per_color": _rival_one_per_color,
    "skip_boundary": _rival_skip_boundary,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _has_trigger(grid: Any) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["plus_count"] >= 1


def _has_l_distractor(grid: Any) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["scene_profile"] == "l_distractor"


def _has_shared_color_l(grid: Any) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and analysis["scene_profile"] == "l_distractor"
        and bool({grid[r][c] for r, c in analysis["remainder"]}
                 & {t["color"] for t in analysis["triggers"]})
    )


def _has_five_cell_l(grid: Any) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and analysis["scene_profile"] == "l_distractor"
        and len(analysis["remainder"]) == 5
    )


def _has_multicolor_cross(grid: Any) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["scene_profile"] == "multicolor_cross"


def _has_repeated_color_triggers(grid: Any) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and analysis["scene_profile"] == "boundary_repeat"
        and analysis["plus_count"] == 2
        and len({t["color"] for t in analysis["triggers"]}) == 1
    )


def _has_boundary_trigger(grid: Any) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and analysis["scene_profile"] == "boundary_repeat"
        and any(t["touches_border"] for t in analysis["triggers"])
    )


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "plus_changes_output": _has_trigger,
    "l_distractor_stays_unfilled": _has_l_distractor,
    "shared_color_l_stays_unfilled": _has_shared_color_l,
    "five_cell_l_stays_unfilled": _has_five_cell_l,
    "multicolor_cross_stays_unfilled": _has_multicolor_cross,
    "repeated_color_centers_both_fire": _has_repeated_color_triggers,
    "border_touching_center_fires": _has_boundary_trigger,
}
WITNESS_RIVALS = {
    "plus_changes_output": ["identity"],
    "l_distractor_stays_unfilled": ["component_bbox"],
    "shared_color_l_stays_unfilled": ["palette_gated_bbox"],
    "five_cell_l_stays_unfilled": ["five_cell_bbox"],
    "multicolor_cross_stays_unfilled": ["color_blind_cross"],
    "repeated_color_centers_both_fire": ["one_per_color"],
    "border_touching_center_fires": ["skip_boundary"],
}


def lesson_identifiable(demos: list[dict[str, Any]],
                        query: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        errors.append(
            f"need at least {EXAMPLES_NEEDED} demonstrations, found {len(demos)}"
        )
    profiles: set[str] = set()
    for label, pair in [
        *( (f"demo[{index}]", pair) for index, pair in enumerate(demos) ),
        ("query", query),
    ]:
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"{label} must contain input and output grids")
            continue
        findings = self_check(pair["input"])
        if findings:
            errors.append(f"{label} input is outside teaching grammar: {findings[:2]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            errors.append(f"{label} output does not match the canonical local rule")
        observed = observe_overrides(pair["input"])
        if label.startswith("demo") and observed:
            profiles.add(observed["scene_profile"])

    missing = sorted(set(SCENE_PROFILES) - profiles)
    if missing:
        errors.append(f"demonstrations miss scene profile(s): {missing}")

    for name, rival in LESSON_COMPETITORS.items():
        if demos and all(
            isinstance(pair, dict)
            and "input" in pair and "output" in pair
            and rival(pair["input"]) == pair["output"]
            for pair in demos
        ):
            errors.append(f"rival {name!r} survives every demonstration")
    return errors


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Targeted malformed scenes used by tests and review evidence."""
    valid = generate(20260727, 1, difficulty="medium")
    analysis = _analysis(valid)
    trigger = analysis["triggers"][0]
    row, col = trigger["center"]
    fixtures: list[tuple[str, list[list[int]]]] = []

    blank = full_grid(len(valid), len(valid[0]), 0)
    fixtures.append(("no trigger", blank))

    missing_arm = copy.deepcopy(valid)
    missing_arm[row - 1][col] = 0
    fixtures.append(("missing plus arm", missing_arm))

    prefilled = copy.deepcopy(valid)
    prefilled[row - 1][col - 1] = trigger["color"]
    fixtures.append(("already-filled diagonal", prefilled))

    extra = copy.deepcopy(valid)
    # Clamping col-2 to zero silently repainted the existing left arm for
    # border-touching pluses. Select a genuinely empty, in-bounds spur cell.
    spur_row, spur_col = next(
        (row + 2 * dr, col + 2 * dc)
        for dr, dc in _CARDINAL
        if 0 <= row + 2 * dr < len(valid)
        and 0 <= col + 2 * dc < len(valid[0])
        and valid[row + 2 * dr][col + 2 * dc] == 0
    )
    extra[spur_row][spur_col] = trigger["color"]
    fixtures.append(("extra same-color spur", extra))

    bad_l = copy.deepcopy(valid)
    # The scheduled sample is l_distractor. Add the missing bbox corner.
    remainder = analysis["remainder"]
    if remainder:
        r0, c0, r1, c1 = _bbox(remainder)
        rr0, cc0 = next(iter(remainder))
        for rr in range(r0, r1 + 1):
            for cc in range(c0, c1 + 1):
                bad_l[rr][cc] = valid[rr0][cc0]
    fixtures.append(("solid distractor bbox", bad_l))

    wrong_color = copy.deepcopy(valid)
    if remainder:
        rr, cc = next(iter(remainder))
        wrong_color[rr][cc] = 1 + valid[rr][cc] % 9
    fixtures.append(("nonmonochrome L distractor", wrong_color))

    return fixtures
