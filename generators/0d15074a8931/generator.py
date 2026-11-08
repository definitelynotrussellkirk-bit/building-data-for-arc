"""Generator for ARC task ``0d15074a8931``.

Every nonzero object is a separated, solid rectangle with odd height and odd
width.  The output keeps exactly the geometric center of each rectangle in the
rectangle's original color and clears every other cell.

The canonical examples use one object per color, so ordinary generated lessons
include repeated colors on separated rectangles.  Repeated-color schedule slots
also place a same-color pair in diagonal contact: the rectangles stay separate
under the intended 4-connectivity, decisively refuting per-color and
8-connected-component shortcuts.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0d15074a8931"
TASK_ID = GENERATOR_ID
VERSION = "2.2.0"
RULE_HASH = "4600d000ebae"
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 4

SUMMARY = (
    "Place two to four separated solid odd-by-odd rectangles on a zero "
    "background. Replace every rectangle by only its geometric center cell, "
    "preserving that rectangle's color."
)

INVARIANTS = [
    "background is 0 and every foreground value is an ARC color 1..9",
    "every foreground object is one solid rectangle with odd height and odd width",
    "rectangles are separated by at least one cardinal background cell",
    "normal draws contain 2..4 rectangles, each at least 3x3",
    "repeated colors may label multiple 4-connected rectangles, including corner contact",
]

COUNTER_HYPOTHESES = [
    "keep one center per foreground color rather than per connected rectangle",
    "merge corner-touching rectangles of the same color using 8-connectivity",
    "keep centers of squares only and discard non-square odd rectangles",
    "apply the rule only to 3x3 rectangles",
    "ignore rectangles that touch the grid boundary",
    "keep only the first two rectangles in reading order",
    "preserve the whole input (identity) or use a fixed output position",
]

COLOR_PATTERNS = ("unique", "reused")
EDGE_PROFILES = ("interior", "touching")
SCHEDULE_PROFILES = ("nonsquare", "repeated_color", "large", "multi_object")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-banded, with recurring canonical 9x11 anchors",
        "valid": "9..16",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-banded, with recurring canonical 9x11 anchors",
        "valid": "9..16",
    },
    "rectangles": {
        "type": "int",
        "default": "scheduled 2..4 by sample_index",
        "valid": "2..4",
    },
    "color_pattern": {
        "type": "str",
        "default": "alternating unique/reused by sample_index",
        "valid": "unique|reused",
    },
    "edge_profile": {
        "type": "str",
        "default": "alternating interior/touching by sample_index",
        "valid": "interior|touching",
    },
}
_ALLOWED_OVERRIDES = frozenset(AXES)

_HEIGHTS_BY_BAND = {
    "easy": (9, 10, 11, 12, 13),
    "medium": (9, 10, 11, 12, 13, 14),
    "hard": (9, 10, 11, 12, 13, 14, 15, 16),
}
_WIDTHS_BY_BAND = {
    "easy": (9, 10, 11, 12, 13),
    "medium": (9, 10, 11, 12, 13, 14, 15),
    "hard": (9, 10, 11, 12, 13, 14, 15, 16),
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _draw_scheduled_int(ctx, label: str, lo: int, hi: int, value: int, overrides: dict[str, Any]) -> int:
    if overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_choice(label, [value])


def _draw_scheduled_choice(ctx, label: str, options: tuple[str, ...], value: str, overrides: dict[str, Any]) -> str:
    if overrides.get(label) is not None:
        return str(ctx.draw_choice(label, options))
    return str(ctx.draw_choice(label, [value]))


def _default_dimension(ctx, label: str, choices: tuple[int, ...], profile: str, sample_index: int, overrides: dict[str, Any]) -> int:
    if overrides.get(label) is not None:
        return ctx.draw_int(label, 9, 16)
    # Every fifth draw is an exact canonical-profile anchor in every band.
    if sample_index % 5 == 0:
        return int(ctx.draw_choice(label, [9 if label == "grid_h" else 11]))
    eligible = list(choices)
    if profile in ("large", "nonsquare"):
        eligible = [value for value in eligible if value >= 13] or [13]
    return int(ctx.draw_choice(label, eligible))


def _quadrant_slots(h: int, w: int) -> list[tuple[int, int, int, int]]:
    """Four disjoint corner slots separated by a central row/column gap."""
    top_h = (h - 1) // 2
    bottom_start = h - top_h
    left_w = (w - 1) // 2
    right_start = w - left_w
    return [
        (0, 0, top_h, left_w),
        (0, right_start, top_h, left_w),
        (bottom_start, 0, top_h, left_w),
        (bottom_start, right_start, top_h, left_w),
    ]


def _odd_sizes(limit: int) -> list[int]:
    return [size for size in (3, 5, 7) if size <= limit]


def _size_options_for_slot(
    slot_h: int,
    slot_w: int,
    profile: str,
    object_index: int,
    rng,
) -> list[tuple[int, int]]:
    """Return randomized sizes with profile-defining shapes before fallbacks."""
    hs = _odd_sizes(slot_h)
    ws = _odd_sizes(slot_w)
    if not hs or not ws:
        raise ValueError(f"slot {slot_h}x{slot_w} cannot contain a 3x3 rectangle")

    all_sizes = [(rh, rw) for rh in hs for rw in ws]
    preferred: list[tuple[int, int]] = []
    if object_index == 0 and profile in ("nonsquare", "large"):
        # Both schedule slots carry both witnesses. Any five consecutive pairs
        # contain at least two such slots, so rotating either one into the query
        # still leaves a non-square, dimension>=5 demonstration.
        preferred = [
            (rh, rw)
            for rh, rw in all_sizes
            if rh != rw and max(rh, rw) >= 5
        ]
    elif object_index == 1 and profile == "multi_object":
        preferred = [(rh, rw) for rh, rw in all_sizes if (rh, rw) != (3, 3)]

    fallback = [size for size in all_sizes if size not in preferred]
    rng.shuffle(preferred)
    rng.shuffle(fallback)
    return [*preferred, *fallback]


def _placement_candidates(
    h: int,
    w: int,
    slot: tuple[int, int, int, int],
    rh: int,
    rw: int,
    *,
    must_touch: bool,
    must_be_interior: bool,
) -> list[tuple[int, int]]:
    sr, sc, sh, sw = slot
    result: list[tuple[int, int]] = []
    for r0 in range(sr, sr + sh - rh + 1):
        for c0 in range(sc, sc + sw - rw + 1):
            touches = r0 == 0 or c0 == 0 or r0 + rh == h or c0 + rw == w
            if must_touch and not touches:
                continue
            if must_be_interior and touches:
                continue
            result.append((r0, c0))
    return result


def _rect_cells(r0: int, c0: int, rh: int = 3, rw: int = 3) -> set[tuple[int, int]]:
    return {(r, c) for r in range(r0, r0 + rh) for c in range(c0, c0 + rw)}


def _cardinally_separated(
    cells: set[tuple[int, int]], others: list[set[tuple[int, int]]]
) -> bool:
    for other in others:
        if cells & other:
            return False
        if any(
            (r + dr, c + dc) in other
            for r, c in cells
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
        ):
            return False
    return True


def _contact_layout(
    h: int, w: int, count: int, edge_profile: str, rng
) -> list[tuple[int, int, int, int]]:
    """Place 3x3 rectangles with the first pair touching at one corner."""
    placements = [(r, c) for r in range(h - 2) for c in range(w - 2)]
    pair_candidates: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for first in placements:
        r0, c0 = first
        for dr, dc in ((3, 3), (3, -3), (-3, 3), (-3, -3)):
            second = (r0 + dr, c0 + dc)
            if second not in placements:
                continue
            pair = (first, second)
            touches = any(
                r == 0 or c == 0 or r + 3 == h or c + 3 == w
                for r, c in pair
            )
            if edge_profile == "touching" and not touches:
                continue
            if edge_profile == "interior" and touches:
                continue
            pair_candidates.append(pair)
    rng.shuffle(pair_candidates)

    all_candidates = list(placements)
    rng.shuffle(all_candidates)

    def extend(
        chosen: list[tuple[int, int]], occupied: list[set[tuple[int, int]]]
    ) -> list[tuple[int, int]] | None:
        if len(chosen) == count:
            return chosen
        for position in all_candidates:
            if position in chosen:
                continue
            r0, c0 = position
            touches = r0 == 0 or c0 == 0 or r0 + 3 == h or c0 + 3 == w
            if edge_profile == "interior" and touches:
                continue
            cells = _rect_cells(r0, c0)
            if not _cardinally_separated(cells, occupied):
                continue
            result = extend([*chosen, position], [*occupied, cells])
            if result is not None:
                return result
        return None

    for first, second in pair_candidates:
        occupied = [_rect_cells(*first), _rect_cells(*second)]
        result = extend([first, second], occupied)
        if result is not None:
            return [(r, c, 3, 3) for r, c in result]
    raise ValueError(
        f"cannot place {count} rectangles with same-color diagonal contact "
        f"for {h}x{w}, {edge_profile=}"
    )


def _colors(ctx, count: int, pattern: str) -> list[int]:
    rng = ctx.draw_rng("colors")
    palette = rng.sample(list(range(1, 10)), count)
    if pattern == "unique":
        return palette
    if pattern == "reused":
        if count == 2:
            return [palette[0], palette[0]]
        return [palette[0], palette[0], *palette[1 : count - 1]]
    raise ValueError(f"unknown color pattern: {pattern!r}")


def _validate_grid(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a nonempty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["rows must be nonempty"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return h, w, ["grid must be rectangular"]
    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"invalid ARC color at ({r},{c}): {value!r}")
    return h, w, errors


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            bbox = (min(rows), min(cols), max(rows), max(cols))
            result.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "bbox": bbox,
                    "height": bbox[2] - bbox[0] + 1,
                    "width": bbox[3] - bbox[1] + 1,
                }
            )
    return sorted(result, key=lambda obj: obj["bbox"])


def _analyze(grid: Any) -> dict[str, Any]:
    h, w, errors = _validate_grid(grid)
    result: dict[str, Any] = {"height": h, "width": w, "errors": errors}
    if errors:
        return result
    rects = _components(grid)
    if not 2 <= len(rects) <= 6:
        errors.append(f"expected 2..6 separated rectangles, found {len(rects)}")
    occupied: list[set[tuple[int, int]]] = []
    for index, obj in enumerate(rects):
        r1, c1, r2, c2 = obj["bbox"]
        expected = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}
        cells = set(obj["cells"])
        occupied.append(cells)
        if cells != expected:
            errors.append(f"object {index} is not a solid rectangle")
        if obj["height"] < 3 or obj["width"] < 3:
            errors.append(f"object {index} must be at least 3x3")
        if obj["height"] % 2 == 0 or obj["width"] % 2 == 0:
            errors.append(
                f"object {index} must have odd dimensions, got {obj['height']}x{obj['width']}"
            )
    for i, cells in enumerate(occupied):
        for j in range(i + 1, len(occupied)):
            other = occupied[j]
            if any(
                (r + dr, c + dc) in other
                for r, c in cells
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
            ):
                errors.append(f"objects {i} and {j} are not separated by background")
    colors = [obj["color"] for obj in rects]
    edge_touching = any(
        r1 == 0 or c1 == 0 or r2 == h - 1 or c2 == w - 1
        for r1, c1, r2, c2 in (obj["bbox"] for obj in rects)
    )
    result.update(
        {
            "rects": rects,
            "rectangles": len(rects),
            "color_pattern": "unique" if len(set(colors)) == len(colors) else "reused",
            "edge_profile": "touching" if edge_touching else "interior",
            "has_nonsquare": any(obj["height"] != obj["width"] for obj in rects),
            "has_large": any(max(obj["height"], obj["width"]) >= 5 for obj in rects),
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid: Any) -> list[str]:
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if not 9 <= analysis["height"] <= 16 or not 9 <= analysis["width"] <= 16:
        errors.append(
            f"canonical-like grid dimensions must be 9..16, got {analysis['height']}x{analysis['width']}"
        )
    if not 2 <= analysis["rectangles"] <= 4:
        errors.append(f"canonical-like lessons use 2..4 rectangles, got {analysis['rectangles']}")
    return errors


def observe_overrides(grid: Any) -> dict[str, int | str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "rectangles": analysis["rectangles"],
        "color_pattern": analysis["color_pattern"],
        "edge_profile": analysis["edge_profile"],
    }


def rule_mirror(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    out = full_grid(analysis["height"], analysis["width"], 0)
    for obj in analysis["rects"]:
        r1, c1, r2, c2 = obj["bbox"]
        out[(r1 + r2) // 2][(c1 + c2) // 2] = obj["color"]
    return out


def _rival_one_center_per_color(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    out = full_grid(analysis["height"], analysis["width"], 0)
    seen: set[int] = set()
    for obj in analysis["rects"]:
        if obj["color"] in seen:
            continue
        seen.add(obj["color"])
        r1, c1, r2, c2 = obj["bbox"]
        out[(r1 + r2) // 2][(c1 + c2) // 2] = obj["color"]
    return out


def _filtered_center_rule(grid: Any, keep: Callable[[dict[str, Any]], bool]) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    out = full_grid(analysis["height"], analysis["width"], 0)
    for obj in analysis["rects"]:
        if keep(obj):
            r1, c1, r2, c2 = obj["bbox"]
            out[(r1 + r2) // 2][(c1 + c2) // 2] = obj["color"]
    return out


def _rival_eight_connected_same_color(grid: Any) -> list[list[int]]:
    """Wrong shortcut: merge corner-touching rectangles of the same color."""
    h, w, errors = _validate_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = full_grid(h, w, 0)
    seen: set[tuple[int, int]] = set()
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = rr + dr, cc + dc
                        if (
                            0 <= nr < h
                            and 0 <= nc < w
                            and (nr, nc) not in seen
                            and grid[nr][nc] == color
                        ):
                            seen.add((nr, nc))
                            queue.append((nr, nc))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            out[(min(rows) + max(rows)) // 2][(min(cols) + max(cols)) // 2] = color
    return out


def _rival_squares_only(grid: Any) -> list[list[int]]:
    return _filtered_center_rule(grid, lambda obj: obj["height"] == obj["width"])


def _rival_three_by_three_only(grid: Any) -> list[list[int]]:
    return _filtered_center_rule(grid, lambda obj: obj["height"] == 3 and obj["width"] == 3)


def _rival_ignore_edge_touching(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    h, w = analysis["height"], analysis["width"]
    return _filtered_center_rule(
        grid,
        lambda obj: not (
            obj["bbox"][0] == 0
            or obj["bbox"][1] == 0
            or obj["bbox"][2] == h - 1
            or obj["bbox"][3] == w - 1
        ),
    )


def _rival_first_two(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    out = full_grid(analysis["height"], analysis["width"], 0)
    for obj in analysis["rects"][:2]:
        r1, c1, r2, c2 = obj["bbox"]
        out[(r1 + r2) // 2][(c1 + c2) // 2] = obj["color"]
    return out


SEMANTIC_RIVALS = {
    "one_center_per_color": _rival_one_center_per_color,
    "eight_connected_same_color": _rival_eight_connected_same_color,
    "squares_only": _rival_squares_only,
    "three_by_three_only": _rival_three_by_three_only,
    "ignore_edge_touching": _rival_ignore_edge_touching,
    "first_two_objects": _rival_first_two,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "one_center_per_color": _rival_one_center_per_color,
    "eight_connected_same_color": _rival_eight_connected_same_color,
}


def _witness_repeated_color(grid: Any) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["color_pattern"] == "reused"


def _witness_same_color_diagonal_contact(grid: Any) -> bool:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return False
    rects = analysis["rects"]
    for index, left in enumerate(rects):
        left_cells = set(left["cells"])
        for right in rects[index + 1 :]:
            if left["color"] != right["color"]:
                continue
            right_cells = set(right["cells"])
            if any(
                (r + dr, c + dc) in right_cells
                for r, c in left_cells
                for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1))
            ):
                return True
    return False


def _witness_nonsquare(grid: Any) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["has_nonsquare"]


def _witness_large(grid: Any) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["has_large"]


def _witness_edge_touching(grid: Any) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["edge_profile"] == "touching"


def _witness_three_or_more(grid: Any) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["rectangles"] >= 3


SEMANTIC_WITNESSES = {
    "repeated_color_components": _witness_repeated_color,
    "same_color_diagonal_contact": _witness_same_color_diagonal_contact,
    "non_square_odd_rectangle": _witness_nonsquare,
    "dimension_five_or_seven": _witness_large,
    "boundary_touching_rectangle": _witness_edge_touching,
    "three_or_more_rectangles": _witness_three_or_more,
}
WITNESS_RIVALS = {
    "repeated_color_components": ["one_center_per_color"],
    "same_color_diagonal_contact": ["eight_connected_same_color"],
    "non_square_odd_rectangle": ["squares_only"],
    "dimension_five_or_seven": ["three_by_three_only"],
    "boundary_touching_rectangle": ["ignore_edge_touching"],
    "three_or_more_rectangles": ["first_two_objects"],
}


def lesson_identifiable(demos, query) -> list[str]:
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    witness_hits = {name: 0 for name in SEMANTIC_WITNESSES}
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        errors = strict_canonical_like(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output does not keep every rectangle center")
        for name, witness in SEMANTIC_WITNESSES.items():
            witness_hits[name] += int(witness(pair["input"]))
    missing = [name for name, hits in witness_hits.items() if hits == 0]
    if missing:
        reasons.append(f"demonstrations do not refute required rivals: {missing}")
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        errors = strict_canonical_like(query["input"])
        if errors:
            reasons.append(f"query malformed: {errors[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output does not match the rectangle-center rule")
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - _ALLOWED_OVERRIDES
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    band = _band(difficulty)
    profile = schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    h = _default_dimension(ctx, "grid_h", _HEIGHTS_BY_BAND[band], profile, sample_index, overrides)
    w = _default_dimension(ctx, "grid_w", _WIDTHS_BY_BAND[band], profile, sample_index, overrides)

    scheduled_count = 2 if sample_index % 5 == 0 else 2 + (sample_index % 3)
    if profile == "multi_object" and sample_index % 5 != 0:
        scheduled_count = max(3, scheduled_count)
    count = _draw_scheduled_int(ctx, "rectangles", 2, 4, scheduled_count, overrides)

    if profile in ("repeated_color", "multi_object") and overrides.get("color_pattern") is None:
        scheduled_colors = "reused"
    else:
        scheduled_colors = "unique" if sample_index % 5 == 0 else COLOR_PATTERNS[sample_index % 2]
    color_pattern = _draw_scheduled_choice(
        ctx, "color_pattern", COLOR_PATTERNS, scheduled_colors, overrides
    )
    scheduled_edge = "touching" if sample_index % 5 == 0 else EDGE_PROFILES[sample_index % 2]
    edge_profile = _draw_scheduled_choice(
        ctx, "edge_profile", EDGE_PROFILES, scheduled_edge, overrides
    )

    rng = ctx.draw_rng("layout")
    colors = _colors(ctx, count, color_pattern)
    grid = full_grid(h, w, 0)

    use_contact_layout = (
        profile in ("repeated_color", "multi_object")
        and color_pattern == "reused"
        and not overrides
    )
    if use_contact_layout:
        rectangles = _contact_layout(h, w, count, edge_profile, rng)
        for (r0, c0, rh, rw), color in zip(rectangles, colors):
            for r in range(r0, r0 + rh):
                for c in range(c0, c0 + rw):
                    grid[r][c] = color
    else:
        slots = _quadrant_slots(h, w)
        selected_slots = rng.sample(slots, count)
        for index, (slot, color) in enumerate(zip(selected_slots, colors)):
            sr, sc, sh, sw = slot
            del sr, sc
            candidates: list[tuple[int, int]] = []
            rh = rw = 3
            for candidate_h, candidate_w in _size_options_for_slot(
                sh, sw, profile, index, rng
            ):
                candidate_positions = _placement_candidates(
                    h,
                    w,
                    slot,
                    candidate_h,
                    candidate_w,
                    must_touch=edge_profile == "touching" and index == 0,
                    must_be_interior=edge_profile == "interior",
                )
                if candidate_positions:
                    rh, rw = candidate_h, candidate_w
                    candidates = candidate_positions
                    break
            if not candidates:
                raise ValueError(
                    f"cannot place rectangle {index} for {h}x{w}, {edge_profile=}, slot={slot}"
                )
            r0, c0 = rng.choice(candidates)
            for r in range(r0, r0 + rh):
                for c in range(c0, c0 + rw):
                    grid[r][c] = color

    errors = self_check(grid)
    if errors:
        raise RuntimeError("internal generator error: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "rectangles": count,
        "color_pattern": color_pattern,
        "edge_profile": edge_profile,
    }
    if observed != expected:
        raise RuntimeError(f"internal axis observation mismatch: {observed} != {expected}")
    return grid
