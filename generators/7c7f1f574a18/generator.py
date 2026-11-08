"""Input generator for 7c7f1f574a18: classify and horizontally dock objects.

The selected Racket rule treats every non-background 4-connected same-colour
component independently.  A component is *closed* when either its bounding box
has no gaps (a solid rectangle) or at least one bounding-box gap region is
strictly interior.  Closed components keep their rows and shape, move flush to
the left, and become colour 2.  Components whose bbox gaps all reach the bbox
boundary are *open*; they move flush right and become colour 3.

Ordinary scenes deliberately carry both closed subtypes, an open almost-ring,
and crossed input positions.  Those examples refute four common shortcuts:
"closed means solid", "closed means hole-bearing", "everything docks to one
side", and "the starting side determines the destination".
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "7c7f1f574a18"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "e048ab46f343"

SUMMARY = (
    "Find same-colour foreground components against the modal background. "
    "A solid bbox or a component with a truly enclosed bbox gap is closed: "
    "preserve its rows/shape, recolour it 2, and dock it left. If every bbox "
    "gap reaches the bbox boundary, recolour it 3 and dock it right. Generated "
    "lessons contain a solid closed object, an irregular hole-bearing closed "
    "object, and an open almost-ring with roles crossing their starting sides."
)

INVARIANTS = [
    "the background is the unique modal colour",
    "foreground objects are 4-connected same-colour components",
    "at least one closed and one open object are present",
    "component row spans are separated so horizontal docking cannot collide",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 19..24; every third draw anchors at 22",
        "valid": "19..24",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 19..26; anchor draws cycle canonical widths",
        "valid": "19..26",
    },
    "n_closed": {
        "type": "int",
        "default": "difficulty-aware 2..3",
        "valid": "2..3",
    },
    "n_open": {
        "type": "int",
        "default": "difficulty-aware 1..2",
        "valid": "1..2",
    },
    "palette_profile": {
        "type": "str",
        "default": "keyed canonical|binary|multicolor; anchors use canonical",
        "valid": "canonical|binary|multicolor",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_WIDTHS = (19, 21, 22, 24, 26)


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty list or tuple")
    rows: list[list[int]] = []
    width: int | None = None
    for row in grid:
        if not isinstance(row, (list, tuple)) or not row:
            raise ValueError("grid rows must be non-empty lists or tuples")
        values = list(row)
        if width is None:
            width = len(values)
        if len(values) != width:
            raise ValueError("grid must be rectangular")
        if any(
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 <= value <= 9
            for value in values
        ):
            raise ValueError("grid values must be integer ARC colours 0..9")
        rows.append(values)
    if len(rows) > 30 or (width or 0) > 30:
        raise ValueError("ARC grid dimensions must not exceed 30")
    return rows


def _modal_background(grid: list[list[int]]) -> int:
    counts = Counter(value for row in grid for value in row)
    highest = max(counts.values())
    winners = sorted(color for color, count in counts.items() if count == highest)
    if len(winners) != 1:
        raise ValueError(f"background mode is tied across colours {winners}")
    return winners[0]


def _gap_regions(
    cells: set[tuple[int, int]], bbox: tuple[int, int, int, int]
) -> list[dict[str, Any]]:
    r0, c0, r1, c1 = bbox
    unseen = {
        (row, col)
        for row in range(r0, r1 + 1)
        for col in range(c0, c1 + 1)
        if (row, col) not in cells
    }
    regions: list[dict[str, Any]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        region = {start}
        touches_boundary = False
        while queue:
            row, col = queue.popleft()
            if row in (r0, r1) or col in (c0, c1):
                touches_boundary = True
            for drow, dcol in _DIR4:
                nxt = row + drow, col + dcol
                if nxt in unseen:
                    unseen.remove(nxt)
                    region.add(nxt)
                    queue.append(nxt)
        regions.append(
            {"cells": region, "touches_boundary": touches_boundary}
        )
    return regions


def _components(
    grid: list[list[int]], background: int
) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            start = (start_row, start_col)
            if color == background or start in seen:
                continue
            queue = deque([start])
            seen.add(start)
            cells: set[tuple[int, int]] = set()
            while queue:
                row, col = queue.popleft()
                cells.add((row, col))
                for drow, dcol in _DIR4:
                    nxt = row + drow, col + dcol
                    nr, nc = nxt
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and nxt not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add(nxt)
                        queue.append(nxt)
            rows = [row for row, _ in cells]
            cols = [col for _, col in cells]
            bbox = min(rows), min(cols), max(rows), max(cols)
            regions = _gap_regions(cells, bbox)
            has_hole = any(not region["touches_boundary"] for region in regions)
            closed = not regions or has_hole
            r0, c0, r1, c1 = bbox
            components.append(
                {
                    "color": color,
                    "cells": cells,
                    "bbox": bbox,
                    "height": r1 - r0 + 1,
                    "width": c1 - c0 + 1,
                    "center_col": (c0 + c1) / 2,
                    "gap_regions": regions,
                    "gap_count": sum(len(region["cells"]) for region in regions),
                    "has_hole": has_hole,
                    "solid_bbox": not regions,
                    "closed": closed,
                }
            )
    return sorted(components, key=lambda obj: (obj["bbox"][0], obj["bbox"][1]))


def _analysis(grid: Any) -> dict[str, Any]:
    try:
        normalized = _coerce_grid(grid)
        background = _modal_background(normalized)
        components = _components(normalized, background)
    except ValueError as exc:
        return {"errors": [str(exc)]}
    return {
        "errors": [],
        "grid": normalized,
        "height": len(normalized),
        "width": len(normalized[0]),
        "background": background,
        "components": components,
        "closed": [obj for obj in components if obj["closed"]],
        "open": [obj for obj in components if not obj["closed"]],
        "foreground_colors": {
            obj["color"] for obj in components
        },
    }


def _normalize_shape(
    cells: Iterable[tuple[int, int]],
) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _rect_frame(height: int, width: int) -> tuple[tuple[int, int], ...]:
    return tuple(
        (row, col)
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    )


def _filled_rect(height: int, width: int) -> tuple[tuple[int, int], ...]:
    return tuple((row, col) for row in range(height) for col in range(width))


def _irregular_hollow() -> tuple[tuple[int, int], ...]:
    # A wide true-hole frame plus an exterior tab.  At 17 cells it overlaps the
    # canonical object scale while remaining non-rectangular and hole-bearing.
    return _normalize_shape((*_rect_frame(3, 7), (1, 7)))


def _open_almost_ring(width: int = 3) -> tuple[tuple[int, int], ...]:
    # Removing a boundary cell connects the bbox interior to the bbox boundary.
    missing = (2, width // 2)
    return tuple(cell for cell in _rect_frame(3, width) if cell != missing)


def _flip_shape(
    shape: Iterable[tuple[int, int]], *, horizontal: bool, vertical: bool
) -> tuple[tuple[int, int], ...]:
    shape = tuple(shape)
    height = max(row for row, _ in shape) + 1
    width = max(col for _, col in shape) + 1
    return _normalize_shape(
        (
            height - 1 - row if vertical else row,
            width - 1 - col if horizontal else col,
        )
        for row, col in shape
    )


def _shape_width(shape: Iterable[tuple[int, int]]) -> int:
    return max(col for _, col in shape) + 1


def _band_tops(height: int, count: int, rng) -> list[int]:
    minimum = 3 * count + (count - 1)
    if height < minimum:
        raise ValueError(
            f"grid_h={height} cannot fit {count} separated three-row objects"
        )
    extra = height - minimum
    slack = [0] * (count + 1)
    for _ in range(extra):
        slack[rng.randrange(count + 1)] += 1
    tops: list[int] = []
    top = slack[0]
    for index in range(count):
        tops.append(top)
        if index + 1 < count:
            top += 4 + slack[index + 1]
    return tops


def _horizontal_start(
    width: int, shape_width: int, role: str, forced_cross: bool, rng
) -> int:
    max_left = width - shape_width
    if forced_cross and role == "closed":
        low = max(0, width // 2)
        return rng.randint(min(low, max_left), max_left)
    if forced_cross and role == "open":
        high = max(0, (width - 1) // 2 - shape_width)
        return rng.randint(0, min(high, max_left))
    return rng.randint(0, max_left)


def _validate_call(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    for name in ("grid_h", "grid_w", "n_closed", "n_open"):
        if name in overrides and overrides[name] is not None:
            value = overrides[name]
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{name} must be an integer")
    if "palette_profile" in overrides and overrides["palette_profile"] is not None:
        if not isinstance(overrides["palette_profile"], str):
            raise ValueError("palette_profile must be a string")


def _palette(ctx, profile: str, count: int) -> tuple[int, list[int]]:
    rng = ctx.draw_rng("palette-values")
    if profile == "canonical":
        return 4, [1] * count
    if profile == "binary":
        background = rng.choice((0, 4, 5, 8))
        foreground = rng.choice([color for color in range(1, 10) if color != background])
        if background == 4 and foreground == 1:
            foreground = 2
        return background, [foreground] * count
    background = rng.choice((0, 4, 5, 8))
    colors = rng.sample([color for color in range(1, 10) if color != background], 3)
    return background, [colors[index % len(colors)] for index in range(count)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    anchor = sample_index % 3 == 0
    if anchor and "grid_h" not in overrides:
        height = ctx.draw_int("grid_h", 22, 22)
    else:
        height = ctx.draw_int_diff("grid_h", 19, 24)
    if anchor and "grid_w" not in overrides:
        width_value = _CANONICAL_WIDTHS[(sample_index // 3) % len(_CANONICAL_WIDTHS)]
        width = ctx.draw_int("grid_w", width_value, width_value)
    else:
        width = ctx.draw_int_diff("grid_w", 19, 26)
    if anchor and "n_closed" not in overrides:
        n_closed = ctx.draw_int("n_closed", 2, 2)
    else:
        n_closed = ctx.draw_int_diff("n_closed", 2, 3)
    if anchor and "n_open" not in overrides:
        n_open = ctx.draw_int("n_open", 1, 1)
    else:
        n_open = ctx.draw_int_diff("n_open", 1, 2)
    if anchor and "palette_profile" not in overrides:
        palette_profile = ctx.draw_choice("palette_profile", ("canonical",))
    else:
        palette_profile = ctx.draw_choice(
            "palette_profile", ("canonical", "binary", "multicolor")
        )

    shape_rng = ctx.draw_rng("shape-variation")
    layout_rng = ctx.draw_rng("layout")

    descriptors: list[dict[str, Any]] = [
        {
            "role": "closed",
            "kind": "hole",
            "shape": _irregular_hollow(),
            "forced_cross": True,
        },
        {
            "role": "closed",
            "kind": "solid",
            "shape": _filled_rect(3, 3),
            "forced_cross": False,
        },
    ]
    if n_closed == 3:
        descriptors.append(
            {
                "role": "closed",
                "kind": "extra",
                "shape": _rect_frame(3, 6),
                "forced_cross": False,
            }
        )
    descriptors.append(
        {
            "role": "open",
            "kind": "open",
            "shape": _open_almost_ring(6),
            "forced_cross": True,
        }
    )
    if n_open == 2:
        descriptors.append(
            {
                "role": "open",
                "kind": "extra-open",
                "shape": _open_almost_ring(7),
                "forced_cross": False,
            }
        )

    for descriptor in descriptors:
        descriptor["shape"] = _flip_shape(
            descriptor["shape"],
            horizontal=bool(shape_rng.randrange(2)),
            vertical=bool(shape_rng.randrange(2)),
        )
    layout_rng.shuffle(descriptors)
    tops = _band_tops(height, len(descriptors), layout_rng)
    background, colors = _palette(ctx, palette_profile, len(descriptors))
    grid = full_grid(height, width, background)
    for index, (descriptor, top) in enumerate(zip(descriptors, tops)):
        shape = descriptor["shape"]
        left = _horizontal_start(
            width,
            _shape_width(shape),
            descriptor["role"],
            descriptor["forced_cross"],
            layout_rng,
        )
        color = colors[index]
        for row, col in shape:
            grid[top + row][left + col] = color
    return grid


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every advertised exact control from returned pixels."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    foreground = analysis["foreground_colors"]
    if analysis["background"] == 4 and foreground == {1}:
        profile = "canonical"
    elif len(foreground) == 1:
        profile = "binary"
    else:
        profile = "multicolor"
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_closed": len(analysis["closed"]),
        "n_open": len(analysis["open"]),
        "palette_profile": profile,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the broad task grammar and any requested exact controls."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    components = analysis["components"]
    if len(components) < 2:
        errors.append("need at least two foreground components")
    if not analysis["closed"]:
        errors.append("need at least one closed component")
    if not analysis["open"]:
        errors.append("need at least one open component")

    ordered = sorted(components, key=lambda obj: obj["bbox"][0])
    for previous, current in zip(ordered, ordered[1:]):
        if current["bbox"][0] <= previous["bbox"][2] + 1:
            errors.append(
                "component row spans must have at least one blank separating row"
            )
            break

    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and name in observed and observed[name] != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed[name]!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Canonical-size/palette teaching predicate; accepts all five source inputs."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    analysis = _analysis(grid)
    if analysis["height"] != 22:
        reasons.append("canonical inputs have height 22")
    if analysis["width"] not in _CANONICAL_WIDTHS:
        reasons.append("width is outside the five canonical widths")
    if analysis["background"] != 4 or analysis["foreground_colors"] != {1}:
        reasons.append("canonical palette is background 4 with foreground 1")
    if not 3 <= len(analysis["components"]) <= 5:
        reasons.append("canonical inputs contain 3..5 components")
    return reasons


def _render_by_classifier(
    grid: Any, classifier: Callable[[dict[str, Any], dict[str, Any]], bool]
) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid grid: " + "; ".join(analysis["errors"]))
    out = full_grid(
        analysis["height"], analysis["width"], analysis["background"]
    )
    for obj in analysis["components"]:
        closed = classifier(obj, analysis)
        destination = 0 if closed else analysis["width"] - obj["width"]
        color = 2 if closed else 3
        _, source_col, _, _ = obj["bbox"]
        for row, col in obj["cells"]:
            out[row][destination + col - source_col] = color
    return out


def rule_true(grid) -> list[list[int]]:
    """Independent Python mirror for tests; Racket remains label authority."""
    return _render_by_classifier(grid, lambda obj, _analysis: obj["closed"])


def _rival_solid_only_closed(grid):
    """Wrong shortcut: only gap-free rectangles count as closed."""
    return _render_by_classifier(grid, lambda obj, _analysis: obj["solid_bbox"])


def _rival_holes_only_closed(grid):
    """Wrong shortcut: a true hole is required, so solid rectangles go right."""
    return _render_by_classifier(grid, lambda obj, _analysis: obj["has_hole"])


def _rival_all_left(grid):
    """Wrong shortcut: ignore topology and dock every object left."""
    return _render_by_classifier(grid, lambda _obj, _analysis: True)


def _rival_all_right(grid):
    """Wrong shortcut: ignore topology and dock every object right."""
    return _render_by_classifier(grid, lambda _obj, _analysis: False)


def _rival_starting_side(grid):
    """Wrong shortcut: objects starting left go left, starting right go right."""
    return _render_by_classifier(
        grid,
        lambda obj, analysis: obj["center_col"] < (analysis["width"] - 1) / 2,
    )


def _witness_true_hole_closed(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and any(
        obj["closed"] and obj["has_hole"] and not obj["solid_bbox"]
        for obj in analysis["components"]
    )


def _witness_solid_closed(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and any(
        obj["closed"] and obj["solid_bbox"] for obj in analysis["components"]
    )


def _witness_open_boundary_gap(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and bool(analysis["open"])


def _witness_crossed_starting_sides(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    midpoint = (analysis["width"] - 1) / 2
    return any(
        obj["closed"] and obj["center_col"] > midpoint
        for obj in analysis["components"]
    ) and any(
        not obj["closed"] and obj["center_col"] < midpoint
        for obj in analysis["components"]
    )


SEMANTIC_WITNESSES = {
    "true_hole_closed": _witness_true_hole_closed,
    "solid_closed": _witness_solid_closed,
    "open_boundary_gap": _witness_open_boundary_gap,
    "crossed_starting_sides": _witness_crossed_starting_sides,
}
BRANCH_WITNESSES = tuple(SEMANTIC_WITNESSES)

SEMANTIC_RIVALS = {
    "solid_only_closed": _rival_solid_only_closed,
    "holes_only_closed": _rival_holes_only_closed,
    "all_left": _rival_all_left,
    "all_right": _rival_all_right,
    "starting_side": _rival_starting_side,
}

WITNESS_RIVALS = {
    "true_hole_closed": ["solid_only_closed", "all_right"],
    "solid_closed": ["holes_only_closed", "all_right"],
    "open_boundary_gap": ["all_left"],
    "crossed_starting_sides": ["starting_side"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# No additional task-local shortcut was found that reproduces all five labeled
# canonical pairs while remaining meaningfully distinct from the selected rule.
CANONICAL_SHORTCUTS: dict[str, Callable[[Any], list[list[int]]]] = {}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson if a named plausible shortcut survives every demo."""
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        expected = rule_true(pair["input"])
        if pair.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with the docking rule")
    query_answer = rule_true(query["input"])
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output disagrees with the docking rule")
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair.get("output") for pair in demos
        )
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons
