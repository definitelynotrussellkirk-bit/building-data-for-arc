"""Generator for ARC task 6e19193c / canonical task 8a802749348c.

Each 4-connected three-cell L inside a 2x2 box has one missing corner.  Extend
that missing-corner diagonal *away* from the opposite occupied corner, starting
one cell beyond the missing corner and continuing to the grid edge in the L's
own color.

The teaching distribution deliberately varies all four L orientations,
separate pieces that reuse one color, pieces with distinct colors, positions,
ray lengths, object counts, and grid sizes.  Rays never cross an input object or
one another, so the intended per-object rule has a unique, order-independent
answer.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8a802749348c"
TASK_ID = "8a802749348c"
VERSION = "2.0.0"
RULE_HASH = "96a0505bb364"

SUMMARY = (
    "Every separated three-cell L emits a same-color diagonal ray away from "
    "its missing 2x2 corner, beginning one cell beyond that missing corner. "
    "The distribution covers all four directions, repeated and distinct "
    "object colors, 1..5 pieces, 8..16 dimensions, varied positions and ray "
    "lengths, with collision-free rays and a 10x10 repeated-color canonical "
    "anchor."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.40

INVARIANTS = [
    "background is color 0 and every nonzero 4-connected component is one L-tromino",
    "each L occupies exactly three corners of a 2x2 bounding box",
    "pieces are orthogonally separated even when their colors differ",
    "every missing corner has at least one outward diagonal cell before the grid edge",
    "outward rays do not hit input pieces and do not intersect one another",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed 8..16 with a deterministic 10x10 canonical anchor",
        "valid": "8..16",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed 8..16 with a deterministic 10x10 canonical anchor",
        "valid": "8..16",
    },
    "object_count": {
        "type": "int",
        "default": "difficulty-skewed 2..5; canonical anchors use 2 or 3",
        "valid": "1..5",
    },
}

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CORNERS = ("tl", "tr", "bl", "br")
_CORNER_OFFSETS = {
    "tl": (0, 0),
    "tr": (0, 1),
    "bl": (1, 0),
    "br": (1, 1),
}
_NONZERO_COLORS = tuple(range(1, 10))


def _copy_grid(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


def _ray_from_missing(
    missing: tuple[int, int],
    direction: tuple[int, int],
    h: int,
    w: int,
    *,
    include_missing: bool = False,
) -> list[tuple[int, int]]:
    dr, dc = direction
    rr, cc = missing if include_missing else (missing[0] + dr, missing[1] + dc)
    ray: list[tuple[int, int]] = []
    while 0 <= rr < h and 0 <= cc < w:
        ray.append((rr, cc))
        rr += dr
        cc += dc
    return ray


def _component_cells(
    grid: list[list[int]], r0: int, c0: int, visited: set[tuple[int, int]]
) -> list[tuple[int, int]]:
    h, w = len(grid), len(grid[0])
    color = grid[r0][c0]
    queue = deque([(r0, c0)])
    visited.add((r0, c0))
    cells: list[tuple[int, int]] = []
    while queue:
        r, c = queue.popleft()
        cells.append((r, c))
        for dr, dc in _DIR4:
            nr, nc = r + dr, c + dc
            if (
                0 <= nr < h
                and 0 <= nc < w
                and (nr, nc) not in visited
                and grid[nr][nc] == color
            ):
                visited.add((nr, nc))
                queue.append((nr, nc))
    return sorted(cells)


def _analyze(grid: Any) -> dict[str, Any]:
    """Parse the complete teaching grammar and return count-backed structure."""
    result: dict[str, Any] = {"errors": [], "pieces": []}
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        result["errors"].append("grid must be a nonempty list of rows")
        return result
    h, w = len(grid), len(grid[0])
    result.update({"h": h, "w": w})
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        result["errors"].append("grid must be rectangular with nonempty rows")
        return result
    if not (8 <= h <= 16 and 8 <= w <= 16):
        result["errors"].append("grid dimensions must both lie in 8..16")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        result["errors"].append("grid colors must be integers in 0..9")
        return result

    visited: set[tuple[int, int]] = set()
    pieces: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in visited:
                continue
            color = grid[r][c]
            cells = _component_cells(grid, r, c, visited)
            if len(cells) != 3:
                result["errors"].append(
                    f"color {color} component at {cells[0]} has size {len(cells)}, expected 3"
                )
                continue
            rmin = min(rr for rr, _ in cells)
            rmax = max(rr for rr, _ in cells)
            cmin = min(cc for _, cc in cells)
            cmax = max(cc for _, cc in cells)
            if (rmax - rmin, cmax - cmin) != (1, 1):
                result["errors"].append(
                    f"color {color} component at {cells[0]} is not three corners of a 2x2 box"
                )
                continue
            box = {
                (rmin, cmin),
                (rmin, cmax),
                (rmax, cmin),
                (rmax, cmax),
            }
            cell_set = set(cells)
            missing_cells = box - cell_set
            if len(missing_cells) != 1:
                result["errors"].append(
                    f"color {color} component at {cells[0]} has no unique missing 2x2 corner"
                )
                continue
            missing = next(iter(missing_cells))
            opposite = (rmin + rmax - missing[0], cmin + cmax - missing[1])
            direction = (missing[0] - opposite[0], missing[1] - opposite[1])
            ray = _ray_from_missing(missing, direction, h, w)
            if not ray:
                result["errors"].append(
                    f"L at {(rmin, cmin)} has no visible cell beyond its missing corner"
                )
            corner = next(
                name
                for name, (dr, dc) in _CORNER_OFFSETS.items()
                if missing == (rmin + dr, cmin + dc)
            )
            pieces.append(
                {
                    "color": color,
                    "cells": tuple(cells),
                    "cell_set": frozenset(cell_set),
                    "bbox": (rmin, cmin, rmax, cmax),
                    "missing": missing,
                    "corner": corner,
                    "direction": direction,
                    "ray": tuple(ray),
                    "ray_set": frozenset(ray),
                }
            )

    pieces.sort(key=lambda obj: (obj["cells"][0], obj["color"]))
    result["pieces"] = pieces
    result["object_count"] = len(pieces)
    result["palette"] = sorted({obj["color"] for obj in pieces})
    if not (1 <= len(pieces) <= 5):
        result["errors"].append(f"expected 1..5 L-trominoes, found {len(pieces)}")

    all_object_cells = set().union(*(obj["cell_set"] for obj in pieces)) if pieces else set()
    for index, obj in enumerate(pieces):
        hit_objects = obj["ray_set"] & all_object_cells
        if hit_objects:
            result["errors"].append(
                f"ray from object {index} intersects input object cells {sorted(hit_objects)}"
            )
        for prior_index, prior in enumerate(pieces[:index]):
            if obj["ray_set"] & prior["ray_set"]:
                result["errors"].append(
                    f"rays from pieces {prior_index} and {index} intersect"
                )
            if any(
                (r + dr, c + dc) in prior["cell_set"]
                for r, c in obj["cells"]
                for dr, dc in _DIR4
            ):
                result["errors"].append(
                    f"pieces {prior_index} and {index} are orthogonally adjacent"
                )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, no-op, or rule-hiding lesson inputs."""
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact axis from the returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["h"],
        "grid_w": analysis["w"],
        "object_count": analysis["object_count"],
    }


def strict_canonical_like(grid) -> list[str]:
    """Recognize the two canonical 10x10 repeated-color object-count profiles."""
    analysis = _analyze(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    if (analysis["h"], analysis["w"]) != (10, 10):
        reasons.append("canonical examples are 10x10")
    if analysis["object_count"] not in (2, 3):
        reasons.append("canonical examples contain two or three L-trominoes")
    if len(analysis["palette"]) != 1:
        reasons.append("canonical examples reuse one color across all L-trominoes")
    return reasons


def _mirror(grid, *, mode: str = "official") -> list[list[int]] | None:
    """Pure Python audit mirror for the official rule and concrete rivals."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    pieces = list(analysis["pieces"])
    out = _copy_grid(grid)
    first_color = pieces[0]["color"]
    seen_colors: set[int] = set()
    for index, obj in enumerate(pieces):
        if mode == "first_object_only" and index > 0:
            continue
        if mode == "first_per_color" and obj["color"] in seen_colors:
            continue
        seen_colors.add(obj["color"])
        if mode.startswith("skip_") and obj["corner"] == mode.removeprefix("skip_"):
            continue

        direction = obj["direction"]
        if mode == "fixed_southeast":
            direction = (1, 1)
        elif mode == "fixed_northwest":
            direction = (-1, -1)
        include_missing = mode == "inclusive_missing"
        ray = _ray_from_missing(
            obj["missing"],
            direction,
            analysis["h"],
            analysis["w"],
            include_missing=include_missing,
        )
        color = first_color if mode == "single_color" else obj["color"]
        for r, c in ray:
            out[r][c] = color
    return out


def _rival(mode: str) -> Callable[[list[list[int]]], list[list[int]]]:
    def solve(grid: list[list[int]]) -> list[list[int]]:
        out = _mirror(grid, mode=mode)
        return _copy_grid(grid) if out is None else out

    return solve


def _valid_analysis(grid) -> dict[str, Any] | None:
    analysis = _analyze(grid)
    return None if analysis["errors"] else analysis


def _has_corner(corner: str) -> Callable[[Any], bool]:
    def predicate(grid: Any) -> bool:
        analysis = _valid_analysis(grid)
        return bool(analysis and any(obj["corner"] == corner for obj in analysis["pieces"]))

    return predicate


def _witness_multiple_objects(grid: Any) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and analysis["object_count"] >= 2)


def _witness_repeated_color(grid: Any) -> bool:
    analysis = _valid_analysis(grid)
    if not analysis:
        return False
    counts = Counter(obj["color"] for obj in analysis["pieces"])
    return any(count >= 2 for count in counts.values())


def _witness_distinct_colors(grid: Any) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and len(analysis["palette"]) >= 2)


def _witness_missing_corner_is_not_painted(grid: Any) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and analysis["pieces"])


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "missing_top_left": _has_corner("tl"),
    "missing_top_right": _has_corner("tr"),
    "missing_bottom_left": _has_corner("bl"),
    "missing_bottom_right": _has_corner("br"),
    "multiple_objects_all_processed": _witness_multiple_objects,
    "repeated_color_separate_components": _witness_repeated_color,
    "distinct_object_colors_preserved": _witness_distinct_colors,
    "ray_starts_beyond_missing_corner": _witness_missing_corner_is_not_painted,
}

SEMANTIC_RIVALS = {
    "skip_tl": _rival("skip_tl"),
    "skip_tr": _rival("skip_tr"),
    "skip_bl": _rival("skip_bl"),
    "skip_br": _rival("skip_br"),
    "first_object_only": _rival("first_object_only"),
    "first_per_color": _rival("first_per_color"),
    "single_color": _rival("single_color"),
    "inclusive_missing": _rival("inclusive_missing"),
    "fixed_southeast": _rival("fixed_southeast"),
    "fixed_northwest": _rival("fixed_northwest"),
}

WITNESS_RIVALS = {
    "missing_top_left": ["skip_tl"],
    "missing_top_right": ["skip_tr"],
    "missing_bottom_left": ["skip_bl"],
    "missing_bottom_right": ["skip_br"],
    "multiple_objects_all_processed": ["first_object_only"],
    "repeated_color_separate_components": ["first_per_color"],
    "distinct_object_colors_preserved": ["single_color"],
    "ray_starts_beyond_missing_corner": ["inclusive_missing"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Require four demonstrations to eliminate every named concrete rival."""
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if _mirror(pair["input"]) != pair["output"]:
            reasons.append(f"official Python audit disagrees with demo {index}")
    if _mirror(query["input"]) != query["output"]:
        reasons.append("official Python audit disagrees with query")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            rival_query = competitor(query["input"])
            if rival_query != query["output"]:
                reasons.append(f"demos do not falsify rival: {name}")
    return reasons


def _candidate_placements(h: int, w: int) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for r0 in range(h - 1):
        for c0 in range(w - 1):
            box = {
                "tl": (r0, c0),
                "tr": (r0, c0 + 1),
                "bl": (r0 + 1, c0),
                "br": (r0 + 1, c0 + 1),
            }
            for corner in _CORNERS:
                missing = box[corner]
                opposite_name = {"tl": "br", "tr": "bl", "bl": "tr", "br": "tl"}[corner]
                opposite = box[opposite_name]
                direction = (missing[0] - opposite[0], missing[1] - opposite[1])
                ray = _ray_from_missing(missing, direction, h, w)
                if not ray:
                    continue
                cells = frozenset(value for name, value in box.items() if name != corner)
                candidates.append(
                    {
                        "r0": r0,
                        "c0": c0,
                        "corner": corner,
                        "missing": missing,
                        "direction": direction,
                        "cells": cells,
                        "ray": frozenset(ray),
                    }
                )
    return candidates


def _placements_compatible(selected: list[dict[str, Any]], candidate: dict[str, Any]) -> bool:
    for prior in selected:
        if candidate["cells"] & prior["cells"]:
            return False
        if candidate["ray"] & prior["cells"] or prior["ray"] & candidate["cells"]:
            return False
        if candidate["ray"] & prior["ray"]:
            return False
        if any(
            (r + dr, c + dc) in prior["cells"]
            for r, c in candidate["cells"]
            for dr, dc in _DIR4
        ):
            return False
    return True


def _choose_placements(h: int, w: int, count: int, desired: list[str], rng) -> list[dict[str, Any]]:
    candidates = _candidate_placements(h, w)
    grouped: dict[str, list[dict[str, Any]]] = {corner: [] for corner in _CORNERS}
    for candidate in candidates:
        grouped[candidate["corner"]].append(candidate)
    for values in grouped.values():
        rng.shuffle(values)

    selected: list[dict[str, Any]] = []

    def search(index: int) -> bool:
        if index == count:
            return True
        for candidate in grouped[desired[index]]:
            if not _placements_compatible(selected, candidate):
                continue
            selected.append(candidate)
            if search(index + 1):
                return True
            selected.pop()
        return False

    if not search(0):
        raise ValueError(
            f"could not place {count} collision-free L-trominoes in {h}x{w} "
            f"for corner schedule {desired}"
        )
    return selected


def _draw_axis_int(ctx, label: str, valid_lo: int, valid_hi: int, default_lo: int, default_hi: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _canonical_anchor(seed: int, sample_index: int) -> bool:
    del seed
    return sample_index % 2 == 0


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    effective = dict(overrides)
    anchor = not overrides and _canonical_anchor(seed, sample_index)
    if anchor:
        effective.update(
            {
                "grid_h": 10,
                "grid_w": 10,
                "object_count": 2 + ((seed + sample_index) & 1),
            }
        )

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    if difficulty == "easy":
        h = _draw_axis_int(ctx, "grid_h", 8, 16, 8, 11)
        w = _draw_axis_int(ctx, "grid_w", 8, 16, 8, 11)
        count = _draw_axis_int(ctx, "object_count", 1, 5, 2, 3)
    elif difficulty == "hard":
        h = _draw_axis_int(ctx, "grid_h", 8, 16, 12, 16)
        w = _draw_axis_int(ctx, "grid_w", 8, 16, 12, 16)
        count = _draw_axis_int(ctx, "object_count", 1, 5, 4, 5)
    else:
        h = _draw_axis_int(ctx, "grid_h", 8, 16, 9, 13)
        w = _draw_axis_int(ctx, "grid_w", 8, 16, 9, 13)
        count = _draw_axis_int(ctx, "object_count", 1, 5, 3, 4)

    rng = ctx.draw_rng("layout")
    corner_offset = sample_index % len(_CORNERS)
    desired = [_CORNERS[(corner_offset + index) % len(_CORNERS)] for index in range(count)]
    placements = _choose_placements(h, w, count, desired, rng)

    if anchor or sample_index % 3 == 0:
        shared = ctx.draw_color("shared_color", exclude={0})
        colors = [shared] * count
    elif sample_index % 3 == 1 or count == 1:
        colors = list(ctx.draw_distinct_colors("colors", n=count, exclude={0}))
    else:
        palette = list(ctx.draw_distinct_colors("colors", n=2, exclude={0}))
        colors = [palette[index % 2] for index in range(count)]
        if count >= 3:
            colors[-1] = palette[0]

    grid = full_grid(h, w, 0)
    for placement, color in zip(placements, colors):
        for r, c in placement["cells"]:
            grid[r][c] = color

    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("constructed invalid teaching grid: " + "; ".join(analysis["errors"]))
    observed = observe_overrides(grid)
    expected = {"grid_h": h, "grid_w": w, "object_count": count}
    if observed != expected:
        raise ValueError(f"axis realization mismatch: expected {expected}, observed {observed}")
    official = _mirror(grid)
    if official is None or official == grid:
        raise ValueError("constructed a no-op lesson")
    return grid
