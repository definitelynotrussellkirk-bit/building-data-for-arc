"""Generator for ARC task 399643e39cf6.

The unchanged Racket authority sorts the two color-9 markers in row-major order,
uses their displacement as a translation vector, removes the markers, and copies
only the lexicographically smallest ordinary object by
(size, bbox-top, bbox-left, color).

This sampler deliberately exposes counterexamples to the two shortcuts left by
the canonical examples ("smallest means topmost" and "smallest means lowest
color") while keeping every advertised override recoverable from returned pixels.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "399643e39cf6"
TASK_ID = GENERATOR_ID
RULE_HASH = "00eb76bc4fb4"
VERSION = "3.0.0"
SUMMARY = (
    "Two row-major color-9 markers define a translation vector. Remove both "
    "markers and copy only the smallest same-color 4-connected object by that "
    "vector; ties are resolved by top row, left column, then color."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
LESSON_SCHEDULE_PERIOD = 4

VECTOR_KINDS = ("canonical", "horizontal", "down_left", "vertical")
SELECTION_KINDS = ("unique", "tie")
SMALL_SHAPES = ("domino", "triomino", "tetromino")
LARGE_SHAPES = ("pentomino", "hexomino", "heptomino")
PALETTE_KINDS = ("canonical", "warm", "cool", "broad")

AXES = {
    "grid_h": {"type": "int", "default": "schedule over 8..10", "valid": "8..10"},
    "grid_w": {"type": "int", "default": "schedule over 9..11", "valid": "9..11"},
    "vector_kind": {
        "type": "str",
        "default": "four-slot lesson schedule",
        "valid": "|".join(VECTOR_KINDS),
    },
    "selection_kind": {
        "type": "str",
        "default": "alternating unique/tie",
        "valid": "|".join(SELECTION_KINDS),
    },
    "small_shape": {
        "type": "str",
        "default": "schedule over three sizes",
        "valid": "|".join(SMALL_SHAPES),
    },
    "large_shape": {
        "type": "str",
        "default": "schedule over three sizes",
        "valid": "|".join(LARGE_SHAPES),
    },
    "palette_kind": {
        "type": "str",
        "default": "canonical anchor plus broad schedule",
        "valid": "|".join(PALETTE_KINDS),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

INVARIANTS = [
    "exactly two color-9 markers whose row-major displacement is nonzero",
    "two or three distinct-color objects; selected object has size 2..4",
    "selected translated cells are in bounds and initially background",
    "production draws keep every object's translated footprint in bounds and empty",
    "production smallest object is neither topmost nor lowest-color",
]

_VECTOR_DELTAS = {
    "canonical": (5, 3),
    "horizontal": (0, 4),
    "down_left": (4, -3),
    "vertical": (4, 0),
}

# Fixed orientations make shape names observable.  The equal-size alternates
# differ geometrically from the selected shapes and are used only in tie scenes.
_SHAPES = {
    "domino": ((0, 0), (0, 1)),
    "triomino": ((0, 0), (0, 1), (1, 0)),
    "tetromino": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "pentomino": ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)),
    # These compact stair-step shapes are connected, do not self-overlap
    # under the horizontal vector, and leave a packable complement for both
    # equal-size competitors on the strict 8x9/canonical boundary.
    "hexomino": ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0)),
    "heptomino": ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0), (2, 1)),
}
_ALT_SHAPES = {
    "domino": ((0, 0), (1, 0)),
    "triomino": ((0, 0), (0, 1), (0, 2)),
    "tetromino": ((0, 0), (0, 1), (1, 0), (1, 1)),
}

# selected, equal-size alternate, larger object.  The selected color is always
# larger than both competitors, so color is not a proxy for size.
_PALETTES = {
    "canonical": (8, 2, 7),
    "warm": (7, 1, 4),
    "cool": (8, 3, 5),
    "broad": (6, 2, 4),
}


def _normalise(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


_SMALL_BY_SIGNATURE = {_normalise(_SHAPES[name]): name for name in SMALL_SHAPES}
_LARGE_BY_SIGNATURE = {_normalise(_SHAPES[name]): name for name in LARGE_SHAPES}


def _components(grid) -> list[dict[str, Any]]:
    """Same-color 4-connected objects in row-major discovery order."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color in (0, 9) or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for nr, nc in ((cr - 1, cc), (cr + 1, cc), (cr, cc - 1), (cr, cc + 1)):
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            cells.sort()
            rows = [point[0] for point in cells]
            cols = [point[1] for point in cells]
            found.append(
                {
                    "color": color,
                    "cells": tuple(cells),
                    "size": len(cells),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return found


def _selection_key(obj: dict[str, Any]) -> tuple[int, int, int, int]:
    return obj["size"], obj["bbox"][0], obj["bbox"][1], obj["color"]


def _marker_facts(grid) -> tuple[tuple[int, int], tuple[tuple[int, int], tuple[int, int]]]:
    markers = tuple(
        sorted(
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == 9
        )
    )
    if len(markers) != 2:
        raise ValueError(f"expected exactly two color-9 markers, found {len(markers)}")
    (r1, c1), (r2, c2) = markers
    delta = (r2 - r1, c2 - c1)
    if delta == (0, 0):
        raise ValueError("marker vector must be nonzero")
    return delta, markers


def _basic_grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors in 0..9 (booleans are not colors)"]
    return []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate canonical inputs and the declared lawful sampler manifold."""
    errors = _basic_grid_errors(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if not 8 <= h <= 10:
        errors.append(f"grid height {h} outside 8..10")
    if not 9 <= w <= 11:
        errors.append(f"grid width {w} outside 9..11")
    try:
        delta, markers = _marker_facts(grid)
    except ValueError as exc:
        errors.append(str(exc))
        return errors

    comps = _components(grid)
    if len(comps) not in (2, 3):
        errors.append(f"expected two or three ordinary objects, found {len(comps)}")
        return errors
    colors = [obj["color"] for obj in comps]
    if len(set(colors)) != len(colors):
        errors.append("each ordinary object must have a distinct color")
    if any(not 2 <= obj["size"] <= 7 for obj in comps):
        errors.append("ordinary object sizes must lie in 2..7")

    chosen = min(comps, key=_selection_key)
    if chosen["size"] > 4:
        errors.append("selected object must have size at most four")
    dr, dc = delta
    targets = tuple((r + dr, c + dc) for r, c in chosen["cells"])
    if not all(0 <= r < h and 0 <= c < w for r, c in targets):
        errors.append("selected translated copy is clipped")
    elif any(grid[r][c] != 0 for r, c in targets):
        errors.append("selected translated copy must land on background")
    if set(targets) & set(markers):
        # The background test above already catches this; retain the specific
        # diagnostic because marker-target overlap is an easy mutation to miss.
        errors.append("selected translated copy overlaps a marker")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def _shape_placements(
    h: int,
    w: int,
    shape: tuple[tuple[int, int], ...],
    delta: tuple[int, int],
) -> tuple[tuple[tuple[int, int], frozenset[tuple[int, int]], frozenset[tuple[int, int]]], ...]:
    max_r = max(r for r, _ in shape)
    max_c = max(c for _, c in shape)
    dr, dc = delta
    placements = []
    for top in range(h - max_r):
        for left in range(w - max_c):
            source = frozenset((top + r, left + c) for r, c in shape)
            target = frozenset((r + dr, c + dc) for r, c in source)
            if not all(0 <= r < h and 0 <= c < w for r, c in target):
                continue
            if source & target:
                continue
            placements.append(((top, left), source, target))
    return tuple(placements)


def _compatible(*placements) -> bool:
    used: set[tuple[int, int]] = set()
    for _, source, target in placements:
        footprint = set(source) | set(target)
        if used & footprint:
            return False
        used |= footprint
    return True


def _marker_pairs(h: int, w: int, delta: tuple[int, int], occupied: set[tuple[int, int]]):
    dr, dc = delta
    pairs = []
    for r in range(h):
        for c in range(w):
            p1 = (r, c)
            p2 = (r + dr, c + dc)
            if not (0 <= p2[0] < h and 0 <= p2[1] < w):
                continue
            # All declared vectors make p1 row-major before p2.  Keep this
            # explicit: marker draw order must equal authority order.
            if not (p1 < p2):
                continue
            if p1 in occupied or p2 in occupied:
                continue
            pairs.append((p1, p2))
    return pairs


@lru_cache(maxsize=512)
def _layout_candidates(
    h: int,
    w: int,
    vector_kind: str,
    selection_kind: str,
    small_shape: str,
    large_shape: str,
):
    """Construct layouts exhaustively; cache only immutable geometry."""
    delta = _VECTOR_DELTAS[vector_kind]
    large_options = _shape_placements(h, w, _SHAPES[large_shape], delta)
    selected_options = _shape_placements(h, w, _SHAPES[small_shape], delta)
    alternate_options = (
        _shape_placements(h, w, _ALT_SHAPES[small_shape], delta)
        if selection_kind == "tie"
        else (None,)
    )
    layouts = []
    for large in large_options:
        for selected in selected_options:
            # This makes the wrong topmost selector choose the larger object.
            if not large[0] < selected[0]:
                continue
            if not _compatible(large, selected):
                continue
            for alternate in alternate_options:
                placements = (large, selected) if alternate is None else (large, selected, alternate)
                if alternate is not None:
                    # The authority must choose selected rather than the equal-
                    # size alternate by bbox position.
                    if not selected[0] < alternate[0]:
                        continue
                    if not _compatible(*placements):
                        continue
                occupied = set().union(*(set(item[1]) | set(item[2]) for item in placements))
                markers = _marker_pairs(h, w, delta, occupied)
                if not markers:
                    continue
                # One marker pair per object arrangement yields more useful
                # positional diversity than filling the cache with marker-only
                # variants of the first arrangement.
                marker_pair = markers[(len(layouts) * 7) % len(markers)]
                layouts.append((large, selected, alternate, marker_pair))
                if len(layouts) >= 256:
                    return tuple(layouts)
    return tuple(layouts)


def _default_axes(sample_index: int, difficulty=None) -> dict[str, Any]:
    slot = sample_index % LESSON_SCHEDULE_PERIOD
    cycle = sample_index // LESSON_SCHEDULE_PERIOD
    band_offset = {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    # Slot 0 is an exact canonical profile in every difficulty band.  The other
    # slots systematically cover all advertised domains without relying on luck.
    if slot == 0:
        h, w, palette = 8, 9, "canonical"
    else:
        h = 8 + ((cycle + slot) % 3)
        w = 9 + ((2 * cycle + slot) % 3)
        palette = PALETTE_KINDS[(cycle + slot) % len(PALETTE_KINDS)]
    return {
        "grid_h": h,
        "grid_w": w,
        "vector_kind": VECTOR_KINDS[slot],
        "selection_kind": SELECTION_KINDS[slot % 2],
        "small_shape": SMALL_SHAPES[(cycle + band_offset) % len(SMALL_SHAPES)],
        "large_shape": LARGE_SHAPES[(cycle + slot + band_offset) % len(LARGE_SHAPES)],
        "palette_kind": palette,
    }


def _validate_call(difficulty, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        if type(difficulty) is not str:
            raise TypeError("difficulty must be None, 'easy', 'medium', or 'hard'")
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in ("grid_h", "grid_w"):
            if type(value) is not int:
                raise TypeError(f"{name} override must be an integer (not bool)")
        elif type(value) is not str:
            raise TypeError(f"{name} override must be a string")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    defaults = _default_axes(sample_index, difficulty)
    effective = dict(overrides)
    for name, value in defaults.items():
        if effective.get(name) is None:
            effective[name] = value
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    h = ctx.draw_int_strict("grid_h", 8, 10)
    w = ctx.draw_int_strict("grid_w", 9, 11)
    vector_kind = ctx.draw_choice("vector_kind", VECTOR_KINDS)
    selection_kind = ctx.draw_choice("selection_kind", SELECTION_KINDS)
    small_shape = ctx.draw_choice("small_shape", SMALL_SHAPES)
    large_shape = ctx.draw_choice("large_shape", LARGE_SHAPES)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)

    layouts = _layout_candidates(h, w, vector_kind, selection_kind, small_shape, large_shape)
    if not layouts:
        raise ValueError(
            "advertised override combination unexpectedly has no constructive layout: "
            f"{h}x{w}, {vector_kind}, {selection_kind}, {small_shape}, {large_shape}"
        )
    large, selected, alternate, markers = ctx.draw_rng(f"layout_{difficulty or 'none'}").choice(layouts)
    selected_color, alternate_color, large_color = _PALETTES[palette_kind]
    grid = full_grid(h, w, 0)
    for r, c in large[1]:
        grid[r][c] = large_color
    for r, c in selected[1]:
        grid[r][c] = selected_color
    if alternate is not None:
        for r, c in alternate[1]:
            grid[r][c] = alternate_color
    for r, c in markers:
        grid[r][c] = 9

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("constructed invalid scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "vector_kind": vector_kind,
        "selection_kind": selection_kind,
        "small_shape": small_shape,
        "large_shape": large_shape,
        "palette_kind": palette_kind,
    }
    if observed != expected:
        raise AssertionError(f"constructed axes {expected!r}, observed {observed!r}")
    return grid


def observe_overrides(grid) -> dict[str, Any]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed scene: " + "; ".join(errors))
    delta, _ = _marker_facts(grid)
    try:
        vector_kind = next(name for name, value in _VECTOR_DELTAS.items() if value == delta)
    except StopIteration as exc:
        raise ValueError(f"unadvertised marker vector {delta}") from exc
    comps = _components(grid)
    selected = min(comps, key=_selection_key)
    largest = max(comps, key=lambda obj: (obj["size"], -obj["bbox"][0], -obj["bbox"][1]))
    selection_kind = "tie" if sum(obj["size"] == selected["size"] for obj in comps) > 1 else "unique"
    small_signature = _normalise(selected["cells"])
    large_signature = _normalise(largest["cells"])
    if small_signature not in _SMALL_BY_SIGNATURE:
        raise ValueError(f"unadvertised selected shape {small_signature}")
    if large_signature not in _LARGE_BY_SIGNATURE:
        raise ValueError(f"unadvertised large shape {large_signature}")
    alternate = None
    if selection_kind == "tie":
        alternate = min(
            (obj for obj in comps if obj is not selected and obj["size"] == selected["size"]),
            key=_selection_key,
        )
    palette_tuple = (selected["color"], alternate["color"] if alternate else None, largest["color"])
    palette_kind = None
    for name, (selected_color, alternate_color, large_color) in _PALETTES.items():
        expected = (selected_color, alternate_color if alternate else None, large_color)
        if palette_tuple == expected:
            palette_kind = name
            break
    if palette_kind is None:
        raise ValueError(f"unadvertised palette roles {palette_tuple}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "vector_kind": vector_kind,
        "selection_kind": selection_kind,
        "small_shape": _SMALL_BY_SIGNATURE[small_signature],
        "large_shape": _LARGE_BY_SIGNATURE[large_signature],
        "palette_kind": palette_kind,
    }


def _paint_copy(out, obj, delta):
    h, w = len(out), len(out[0])
    dr, dc = delta
    for r, c in obj["cells"]:
        rr, cc = r + dr, c + dc
        if 0 <= rr < h and 0 <= cc < w:
            out[rr][cc] = obj["color"]


def _rule_variant(
    grid,
    *,
    selector="smallest",
    vector_mode="markers",
    remove_markers=True,
    copy_all=False,
):
    out = [list(row) for row in grid]
    delta, markers = _marker_facts(grid)
    if vector_mode == "reverse":
        delta = (-delta[0], -delta[1])
    elif vector_mode == "canonical":
        delta = _VECTOR_DELTAS["canonical"]
    elif vector_mode != "markers":
        raise ValueError(vector_mode)
    if remove_markers:
        for r, c in markers:
            out[r][c] = 0
    comps = _components(grid)
    if copy_all:
        selected = comps
    elif selector == "smallest":
        selected = [min(comps, key=_selection_key)]
    elif selector == "topmost":
        selected = [min(comps, key=lambda obj: (obj["bbox"][0], obj["bbox"][1], obj["color"]))]
    elif selector == "lowest_color":
        selected = [min(comps, key=lambda obj: (obj["color"], obj["bbox"][0], obj["bbox"][1]))]
    elif selector == "largest":
        selected = [min(comps, key=lambda obj: (-obj["size"], obj["bbox"][0], obj["bbox"][1], obj["color"]))]
    elif selector == "reverse_tie":
        minimum = min(obj["size"] for obj in comps)
        selected = [max(
            (obj for obj in comps if obj["size"] == minimum),
            key=lambda obj: (obj["bbox"][0], obj["bbox"][1], obj["color"]),
        )]
    else:
        raise ValueError(selector)
    for obj in selected:
        _paint_copy(out, obj, delta)
    return out


def rule_smallest(grid):
    return _rule_variant(grid)


def _topmost_object(grid):
    return _rule_variant(grid, selector="topmost")


def _lowest_color_object(grid):
    return _rule_variant(grid, selector="lowest_color")


def _largest_object(grid):
    return _rule_variant(grid, selector="largest")


def _all_objects(grid):
    return _rule_variant(grid, copy_all=True)


def _reverse_tie_break(grid):
    return _rule_variant(grid, selector="reverse_tie")


def _keep_markers(grid):
    return _rule_variant(grid, remove_markers=False)


def _reverse_vector(grid):
    return _rule_variant(grid, vector_mode="reverse")


def _fixed_canonical_vector(grid):
    return _rule_variant(grid, vector_mode="canonical")


def _facts(grid):
    comps = _components(grid)
    selected = min(comps, key=_selection_key)
    topmost = min(comps, key=lambda obj: (obj["bbox"][0], obj["bbox"][1], obj["color"]))
    lowest = min(comps, key=lambda obj: (obj["color"], obj["bbox"][0], obj["bbox"][1]))
    delta, markers = _marker_facts(grid)
    h, w = len(grid), len(grid[0])
    occupied = {point for obj in comps for point in obj["cells"]} | set(markers)
    every_copy_clear = True
    for obj in comps:
        targets = {(r + delta[0], c + delta[1]) for r, c in obj["cells"]}
        every_copy_clear &= all(0 <= r < h and 0 <= c < w for r, c in targets)
        every_copy_clear &= not bool(targets & occupied)
    return {
        "selected_not_topmost": selected is not topmost,
        "selected_not_lowest": selected is not lowest,
        "all_copy_footprints_clear": every_copy_clear,
        "noncanonical_vector": delta != _VECTOR_DELTAS["canonical"],
        "selection_tie": sum(obj["size"] == selected["size"] for obj in comps) > 1,
    }


def _witness(name):
    def predicate(grid):
        try:
            return bool(_facts(grid)[name])
        except Exception:
            return False
    return predicate


SEMANTIC_WITNESSES = {
    "selected_not_topmost": _witness("selected_not_topmost"),
    "selected_not_lowest": _witness("selected_not_lowest"),
    "all_copy_footprints_clear": _witness("all_copy_footprints_clear"),
    "noncanonical_vector": _witness("noncanonical_vector"),
    "selection_tie": _witness("selection_tie"),
}
SEMANTIC_RIVALS = {
    "topmost_object": _topmost_object,
    "lowest_color_object": _lowest_color_object,
    "largest_object": _largest_object,
    "all_objects": _all_objects,
    "reverse_tie_break": _reverse_tie_break,
    "keep_markers": _keep_markers,
    "reverse_vector": _reverse_vector,
    "fixed_canonical_vector": _fixed_canonical_vector,
}
WITNESS_RIVALS = {
    "selected_not_topmost": ["topmost_object"],
    "selected_not_lowest": ["lowest_color_object"],
    "all_copy_footprints_clear": ["largest_object", "all_objects"],
    "noncanonical_vector": ["fixed_canonical_vector"],
    "selection_tie": ["reverse_tie_break"],
}
CANONICAL_SHORTCUTS = {
    "topmost_object": _topmost_object,
    "lowest_color_object": _lowest_color_object,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Return reasons a visible lesson still permits a declared rival."""
    reasons: list[str] = []
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    valid_demos = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        if rule_smallest(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output disagrees with the pinned rule")
            continue
        valid_demos.append(pair)
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        errors = self_check(query["input"])
        if errors:
            reasons.append(f"query malformed: {errors[0]}")
        if "output" in query and rule_smallest(query["input"]) != query["output"]:
            reasons.append("query output disagrees with the pinned rule")
    if len(valid_demos) == len(demos):
        for name, rival in LESSON_COMPETITORS.items():
            if all(rival(pair["input"]) == pair["output"] for pair in valid_demos):
                reasons.append(f"declared rival {name!r} still fits every demonstration")
    return reasons
