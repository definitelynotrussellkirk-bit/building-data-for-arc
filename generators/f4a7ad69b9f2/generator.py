"""Generator for medium_p05 — crop objects, sort by width/height/lex, pack.

Authoritative rule (`obj-width-gallery<`): find each separated monochrome
4-connected nonzero object, crop it to its tight bounding box, sort crops by
``(bbox width, bbox height, lexicographic full crop contents)`` ascending, and
pack them left-to-right, top-aligned, with exactly one 0-column between crops.

The official examples already force the width and height keys.  They do NOT
falsify a plausible ``(width, height, color)`` final tie-break, because the one
equal-dimension canonical pair happens to have lexicographic and color order
aligned.  The generated curriculum therefore schedules four lesson profiles:
width-primary, height-tie, geometry-driven lex tie, and color-driven lex tie.
The six-slot curriculum duplicates both lexicographic profiles and makes both
width profiles refute the width and height shortcuts. Five demonstrations plus
one query therefore remain identifiable under every legal query rotation.
"""
from __future__ import annotations

from itertools import permutations
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f4a7ad69b9f2"
TASK_ID = GENERATOR_ID
VERSION = "3.3.0"
RULE_HASH = "16e822df83e5"
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 0.95

SUMMARY = (
    "Exactly three separated monochrome objects on background 0. Crop each to "
    "its tight bbox, sort by (bbox width ASC, bbox height ASC, full crop "
    "lexicographic contents ASC), then pack left-to-right, top-aligned, with "
    "one background column between crops. Generated lessons explicitly cover "
    "width-primary, height-tie, geometry-driven lex, and color-driven lex "
    "comparisons."
)

INVARIANTS = [
    "background is 0",
    "exactly three 4-connected monochrome objects in distinct colors",
    "the packed oracle output is at most 30x30",
    "ordinary lessons make the scheduled comparator key observable",
]

CANVAS_PROFILES = ("9x12", "10x13", "10x14", "11x15")
LESSON_PROFILES = (
    "width_primary",
    "height_tie",
    "lex_shape",
    "lex_color",
)
_SCHEDULE = (
    "width_primary",
    "height_tie",
    "lex_shape",
    "lex_shape",
    "lex_color",
    "lex_color",
)
SCHEDULE_PROFILES = tuple(
    f"slot{index}:{profile}" for index, profile in enumerate(_SCHEDULE)
)

AXES = {
    "canvas": {
        "type": "str",
        "default": "rng canonical canvas profile",
        "valid": "|".join(CANVAS_PROFILES),
    },
    "lesson_profile": {
        "type": "str",
        "default": "six-slot rotation-robust semantic schedule",
        "valid": "|".join(LESSON_PROFILES),
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))
Shape = tuple[tuple[int, int], ...]


def _shape(*rows: str) -> Shape:
    return tuple(
        (r, c)
        for r, row in enumerate(rows)
        for c, value in enumerate(row)
        if value == "1"
    )


# Normalized shapes from the official examples.  They are sampled as a strong
# morphology prior for the two profiles that canonical already identifies.
_CANONICAL_WIDTH_PROFILES: tuple[tuple[Shape, Shape, Shape], ...] = (
    (
        _shape("10", "10", "11"),
        _shape("111", "101", "111"),
        _shape("1111"),
    ),
    (
        _shape("1"),
        _shape("11", "11", "10"),
        _shape("1111", "1001", "1001", "1111"),
    ),
)
_CANONICAL_HEIGHT_PROFILES: tuple[tuple[Shape, Shape, Shape], ...] = (
    (
        _shape("11", "11"),
        _shape("101", "111"),
        _shape("010", "111", "010"),
    ),
)


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _normalize(cells: Iterable[tuple[int, int]]) -> Shape:
    cells = tuple(cells)
    r1, c1, _r2, _c2 = _bbox(cells)
    return tuple(sorted((r - r1, c - c1) for r, c in cells))


def _shape_size(shape: Shape) -> tuple[int, int]:
    r1, c1, r2, c2 = _bbox(shape)
    return r2 - r1 + 1, c2 - c1 + 1


def _binary_flat(shape: Shape) -> tuple[int, ...]:
    height, width = _shape_size(shape)
    cells = set(_normalize(shape))
    return tuple(
        1 if (r, c) in cells else 0
        for r in range(height)
        for c in range(width)
    )


def _components(grid: list[list[int]]) -> list[dict[str, object]]:
    """Monochrome 4-connected nonzero components, matching this task grammar."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen: set[tuple[int, int]] = set()
    out: list[dict[str, object]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
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
                        stack.append((nr, nc))
            r1, c1, r2, c2 = _bbox(cells)
            out.append(
                {
                    "color": int(color),
                    "cells": tuple(sorted(cells)),
                    "top": r1,
                    "left": c1,
                    "height": r2 - r1 + 1,
                    "width": c2 - c1 + 1,
                }
            )
    return out


def _component_crop(component: dict[str, object]) -> list[list[int]]:
    height = int(component["height"])
    width = int(component["width"])
    top = int(component["top"])
    left = int(component["left"])
    color = int(component["color"])
    crop = full_grid(height, width, 0)
    for r, c in component["cells"]:  # type: ignore[assignment]
        crop[r - top][c - left] = color
    return crop


def _crop_flat(component: dict[str, object]) -> tuple[int, ...]:
    return tuple(value for row in _component_crop(component) for value in row)


def _binary_crop_flat(component: dict[str, object]) -> tuple[int, ...]:
    return tuple(1 if value else 0 for value in _crop_flat(component))


def _official_sort_key(component: dict[str, object]):
    return (
        int(component["width"]),
        int(component["height"]),
        _crop_flat(component),
    )


def _render_components(
    grid: list[list[int]],
    *,
    order: str = "official",
    vertical: str = "top",
    gap: int = 1,
) -> list[list[int]]:
    components = sorted(
        _components(grid),
        key=lambda component: (
            int(component["left"]),
            int(component["top"]),
            int(component["color"]),
        ),
    )
    if not components:
        return [[0]]

    if order == "official":
        components.sort(key=_official_sort_key)
    elif order == "left_to_right":
        pass
    elif order == "color":
        components.sort(key=lambda component: int(component["color"]))
    elif order == "width":
        components.sort(key=lambda component: int(component["width"]))
    elif order == "width_color":
        components.sort(
            key=lambda component: (
                int(component["width"]),
                int(component["color"]),
            )
        )
    elif order == "width_height_color":
        components.sort(
            key=lambda component: (
                int(component["width"]),
                int(component["height"]),
                int(component["color"]),
            )
        )
    elif order == "width_height_shape":
        # Deliberately ignores the nonzero color values in the lex key.  Python
        # stable sorting retains left-to-right order for identical silhouettes.
        components.sort(
            key=lambda component: (
                int(component["width"]),
                int(component["height"]),
                _binary_crop_flat(component),
            )
        )
    elif order == "width_height_first_cell_color":
        # Plausible underspecified shortcut: inspect only the crop's first cell,
        # then fall back to object color instead of scanning the complete crop.
        components.sort(
            key=lambda component: (
                int(component["width"]),
                int(component["height"]),
                _crop_flat(component)[0],
                int(component["color"]),
            )
        )
    elif order == "width_height_first_two_cells_color":
        # A slightly deeper bounded-prefix shortcut.  This still fails to
        # implement full lexicographic comparison when the first distinction
        # occurs at the crop's third or later cell.
        components.sort(
            key=lambda component: (
                int(component["width"]),
                int(component["height"]),
                _crop_flat(component)[:2],
                int(component["color"]),
            )
        )
    else:
        raise ValueError(f"unknown crop order: {order}")

    out_h = max(int(component["height"]) for component in components)
    out_w = sum(int(component["width"]) for component in components) + gap * max(
        0, len(components) - 1
    )
    output = full_grid(out_h, out_w, 0)
    left = 0
    for component in components:
        crop = _component_crop(component)
        if vertical == "top":
            top = 0
        elif vertical == "bottom":
            top = out_h - len(crop)
        else:
            raise ValueError(f"unknown vertical alignment: {vertical}")
        for r, row in enumerate(crop):
            for c, value in enumerate(row):
                output[top + r][left + c] = value
        left += len(crop[0]) + gap
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python audit mirror; Racket remains the output authority."""
    return _render_components(grid)


def _rival_left_to_right(grid):
    return _render_components(grid, order="left_to_right")


def _rival_color_only(grid):
    return _render_components(grid, order="color")


def _rival_width_only(grid):
    return _render_components(grid, order="width")


def _rival_width_then_color(grid):
    return _render_components(grid, order="width_color")


def _rival_width_height_color(grid):
    return _render_components(grid, order="width_height_color")


def _rival_width_height_shape_only(grid):
    return _render_components(grid, order="width_height_shape")


def _rival_width_height_first_cell_then_color(grid):
    return _render_components(grid, order="width_height_first_cell_color")


def _rival_width_height_first_two_cells_then_color(grid):
    return _render_components(grid, order="width_height_first_two_cells_color")


def _rival_bottom_align(grid):
    return _render_components(grid, vertical="bottom")


def _rival_no_gap(grid):
    return _render_components(grid, gap=0)


def _lesson_from_components(components: list[dict[str, object]]) -> str:
    equal_dim_pairs = [
        (a, b)
        for index, a in enumerate(components)
        for b in components[index + 1 :]
        if int(a["width"]) == int(b["width"])
        and int(a["height"]) == int(b["height"])
    ]
    if equal_dim_pairs:
        if any(
            _binary_crop_flat(a) == _binary_crop_flat(b)
            for a, b in equal_dim_pairs
        ):
            return "lex_color"
        return "lex_shape"
    equal_width_pairs = [
        (a, b)
        for index, a in enumerate(components)
        for b in components[index + 1 :]
        if int(a["width"]) == int(b["width"])
        and int(a["height"]) != int(b["height"])
    ]
    if equal_width_pairs:
        # Generated width-primary rows use a repeated width 4; height-tie rows
        # use repeated width 3. Both rows exercise both comparator levels, while
        # the signature keeps exact lesson_profile overrides observable.
        repeated_widths = {int(a["width"]) for a, _ in equal_width_pairs}
        return "width_primary" if 4 in repeated_widths else "height_tie"
    return "width_primary"


def observe_overrides(grid: list[list[int]]) -> dict[str, str]:
    """Recover every declared exact axis directly from the returned grid."""
    return {
        "canvas": f"{len(grid)}x{len(grid[0])}",
        "lesson_profile": _lesson_from_components(_components(grid)),
    }


def _validate_override_keys(overrides: dict[str, object]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis name(s): {', '.join(unknown)}")


def _random_exact_bbox_shape(
    rng,
    height: int,
    width: int,
    *,
    top_left: bool | None = None,
) -> Shape:
    """Connected varied bitmap that touches all four bbox sides exactly."""
    if height < 1 or width < 1:
        raise ValueError("shape dimensions must be positive")
    if height == 1 and width == 1:
        return ((0, 0),)

    # A monotone corner-to-opposite-corner path guarantees connectivity and
    # exact bbox coverage.  Starting top-right leaves top-left empty when the
    # lex-shape lesson needs a geometry-first discriminator.
    force_first_down = False
    if top_left is False and width > 1:
        if height < 2:
            raise ValueError("top-left-empty exact bbox requires height >= 2")
        start = (0, width - 1)
        row_step, col_step = 1, -1
        blocked = {(0, 0)}
        force_first_down = True
    else:
        start = (0, 0)
        row_step, col_step = 1, 1
        blocked: set[tuple[int, int]] = set()

    steps = [(row_step, 0)] * (height - 1) + [(0, col_step)] * (width - 1)
    if force_first_down:
        steps.remove((row_step, 0))
    rng.shuffle(steps)
    if force_first_down:
        steps.insert(0, (row_step, 0))
    cells = {start}
    r, c = start
    for dr, dc in steps:
        r += dr
        c += dc
        cells.add((r, c))

    max_area = height * width - len(blocked)
    lower = len(cells)
    target = rng.randint(lower, max(lower, max_area - 1))
    while len(cells) < target:
        frontier = sorted(
            {
                (r + dr, c + dc)
                for r, c in cells
                for dr, dc in _CARDINAL
                if 0 <= r + dr < height
                and 0 <= c + dc < width
                and (r + dr, c + dc) not in cells
                and (r + dr, c + dc) not in blocked
            }
        )
        if not frontier:
            break
        cells.add(rng.choice(frontier))

    if top_left is True:
        cells.add((0, 0))
    if top_left is False:
        cells.discard((0, 0))
    shape = _normalize(cells)
    if _shape_size(shape) != (height, width):
        raise ValueError("procedural shape lost its requested bounding box")
    return shape


def _random_delayed_prefix_shape(
    rng,
    height: int,
    width: int,
    first_top_column: int,
) -> Shape:
    """Connected exact-bbox shape with a controlled initial flat prefix.

    A vertical stem plus the complete bottom row guarantees connectivity and
    exact bounding-box support.  Blocking the earlier top-row cells creates a
    shared zero prefix for lexicographic lessons; random frontier growth keeps
    the morphology varied without changing that decisive prefix.
    """
    if height < 2 or width < 2:
        raise ValueError("delayed-prefix shapes need at least a 2x2 box")
    if not 1 <= first_top_column < width:
        raise ValueError("first top-row column must lie inside the crop")

    blocked = {(0, column) for column in range(first_top_column)}
    cells = {(row, first_top_column) for row in range(height)}
    cells.update((height - 1, column) for column in range(width))

    max_area = height * width - len(blocked)
    target = rng.randint(len(cells), max(len(cells), max_area - 1))
    while len(cells) < target:
        frontier = sorted(
            {
                (row + dr, column + dc)
                for row, column in cells
                for dr, dc in _CARDINAL
                if 0 <= row + dr < height
                and 0 <= column + dc < width
                and (row + dr, column + dc) not in cells
                and (row + dr, column + dc) not in blocked
            }
        )
        if not frontier:
            break
        cells.add(rng.choice(frontier))

    shape = _normalize(cells)
    if _shape_size(shape) != (height, width):
        raise ValueError("delayed-prefix shape lost its requested bounding box")
    flat = _binary_flat(shape)
    expected_prefix = (0,) * first_top_column + (1,)
    if flat[: first_top_column + 1] != expected_prefix:
        raise ValueError("delayed-prefix shape did not realize its prefix")
    return shape


def _procedural_shapes(profile: str, rng) -> tuple[Shape, Shape, Shape]:
    if profile == "width_primary":
        # Width 2 sorts before the tied width-4 pair; the pair's unequal
        # heights simultaneously supplies the secondary height discriminator.
        specs = ((2, 4), (4, 4), (3, 2))
        return tuple(
            _random_exact_bbox_shape(rng, height, width)
            for height, width in specs
        )  # type: ignore[return-value]
    if profile == "height_tie":
        specs = ((2, 3), (4, 3), (3, 2))
        return tuple(
            _random_exact_bbox_shape(rng, height, width)
            for height, width in specs
        )  # type: ignore[return-value]
    if profile == "lex_shape":
        # Both tied 3x4 crops start with two zeros.  Their first difference is
        # delayed until flat index 2: shape 0 becomes nonzero there, while
        # shape 1 remains zero until index 3.  This refutes bounded one- and
        # two-cell prefix shortcuts rather than merely moving the leak once.
        first = _random_delayed_prefix_shape(rng, 3, 4, 2)
        second = _random_delayed_prefix_shape(rng, 3, 4, 3)
        third = _random_exact_bbox_shape(rng, 2, 2)
        return first, second, third
    if profile == "lex_color":
        tied = _random_exact_bbox_shape(rng, 3, 3)
        third = _random_exact_bbox_shape(rng, 2, 4)
        return tied, tied, third
    raise ValueError(f"unknown lesson profile: {profile}")


def _select_shapes(profile: str, rng, difficulty: str | None) -> tuple[Shape, Shape, Shape]:
    # Canonical morphology remains a substantial prior where it already gives a
    # decisive lesson; procedural rows provide the counterexamples canonical
    # lacks and broaden object texture without changing the task grammar.
    anchor_prob = {"easy": 0.60, "medium": 0.35, "hard": 0.20}.get(
        difficulty, 0.35
    )
    # Width-primary is deliberately procedural: its repeated width-4 pair is
    # what makes the row carry both width and height evidence. Canonical width
    # anchors have three distinct widths and would break rotation robustness.
    if profile == "height_tie" and rng.random() < anchor_prob:
        return tuple(rng.choice(_CANONICAL_HEIGHT_PROFILES))
    return _procedural_shapes(profile, rng)


def _item(shape: Shape, color: int) -> dict[str, object]:
    height, width = _shape_size(shape)
    crop_flat = tuple(color if bit else 0 for bit in _binary_flat(shape))
    return {
        "shape": shape,
        "color": color,
        "height": height,
        "width": width,
        "sort_key": (width, height, crop_flat),
    }


def _assign_colors(profile: str, shapes: tuple[Shape, Shape, Shape], rng):
    low, mid, high = sorted(rng.sample(range(1, 10), 3))
    dims = [_shape_size(shape) for shape in shapes]

    if profile in ("width_primary", "height_tie"):
        width_counts = {width: sum(1 for _, w in dims if w == width) for _, width in dims}
        tied_width = next(width for width, count in width_counts.items() if count == 2)
        tied = [i for i in range(3) if dims[i][1] == tied_width]
        tied.sort(key=lambda i: dims[i][0])
        colors = [mid, mid, mid]
        colors[tied[0]] = high  # shorter should sort first, but gets larger color
        colors[tied[1]] = low
        other = next(i for i in range(3) if i not in tied)
        colors[other] = mid
    elif profile == "lex_shape":
        # Both shapes begin with two zeros, but shape 0 becomes nonzero one cell
        # sooner.  Official lex therefore puts high-colored shape 1 first even
        # though one- or two-cell-prefix-then-color shortcuts put low-colored
        # shape 0 first.
        colors = [low, high, mid]
    elif profile == "lex_color":
        # Identical silhouettes: full crop lex reduces to the nonzero color.
        colors = [low, high, mid]
    else:
        raise ValueError(f"unknown lesson profile: {profile}")
    return [_item(shape, color) for shape, color in zip(shapes, colors)]


def _critical_pair(profile: str, items: list[dict[str, object]]) -> tuple[int, int] | None:
    if profile in ("width_primary", "height_tie"):
        width_counts = {
            width: sum(1 for item in items if int(item["width"]) == width)
            for width in {int(item["width"]) for item in items}
        }
        tied_width = next(width for width, count in width_counts.items() if count == 2)
        pair = [i for i, item in enumerate(items) if int(item["width"]) == tied_width]
        pair.sort(key=lambda i: int(items[i]["height"]))
        return pair[0], pair[1]
    if profile == "lex_color":
        pair = [
            i
            for i in range(3)
            if any(
                i != j
                and int(items[i]["width"]) == int(items[j]["width"])
                and int(items[i]["height"]) == int(items[j]["height"])
                and _binary_flat(items[i]["shape"]) == _binary_flat(items[j]["shape"])  # type: ignore[arg-type]
                for j in range(3)
            )
        ]
        pair.sort(key=lambda i: int(items[i]["color"]))
        return pair[0], pair[1]
    return None


def _paint_layout(
    grid: list[list[int]],
    items: list[dict[str, object]],
    profile: str,
    rng,
) -> None:
    h, w = len(grid), len(grid[0])
    official = tuple(sorted(range(3), key=lambda i: items[i]["sort_key"]))
    critical = _critical_pair(profile, items)
    orders = []
    for order in permutations(range(3)):
        if order == official:
            continue
        if critical is not None:
            earlier, later = critical
            # Reverse the decisive pair in the input's left-to-right order so a
            # stable shortcut cannot accidentally agree with the oracle.
            if order.index(later) > order.index(earlier):
                continue
        orders.append(order)
    input_order = rng.choice(orders)

    minimum_width = sum(int(items[i]["width"]) for i in input_order) + 2
    if minimum_width > w:
        raise ValueError(
            f"object crops need {minimum_width} columns but canvas width is {w}"
        )
    slack = w - minimum_width
    allocations = [0, 0, 0, 0]
    for _ in range(slack):
        allocations[rng.randrange(4)] += 1
    left = allocations[0]

    for position, index in enumerate(input_order):
        item = items[index]
        height = int(item["height"])
        top = rng.randint(0, h - height)
        color = int(item["color"])
        for dr, dc in item["shape"]:  # type: ignore[assignment]
            grid[top + dr][left + dc] = color
        if position < 2:
            left += int(item["width"]) + 1 + allocations[position + 1]


def _lawful(grid: list[list[int]]) -> bool:
    return not self_check(grid)


def _width_primary_witness(grid: list[list[int]]) -> bool:
    components = _components(grid)
    return (
        _lawful(grid)
        and _lesson_from_components(components) in {"width_primary", "height_tie"}
        and _rival_color_only(grid) != rule_mirror(grid)
    )


def _height_tie_witness(grid: list[list[int]]) -> bool:
    return (
        _lawful(grid)
        and _lesson_from_components(_components(grid)) in {"width_primary", "height_tie"}
        and _rival_width_then_color(grid) != rule_mirror(grid)
    )


def _lex_shape_witness(grid: list[list[int]]) -> bool:
    return (
        _lawful(grid)
        and _lesson_from_components(_components(grid)) == "lex_shape"
        and _rival_width_height_color(grid) != rule_mirror(grid)
    )


def _lex_color_witness(grid: list[list[int]]) -> bool:
    return (
        _lawful(grid)
        and _lesson_from_components(_components(grid)) == "lex_color"
        and _rival_width_height_shape_only(grid) != rule_mirror(grid)
    )


def _left_to_right_witness(grid: list[list[int]]) -> bool:
    return _lawful(grid) and _rival_left_to_right(grid) != rule_mirror(grid)


def _top_alignment_witness(grid: list[list[int]]) -> bool:
    heights = [int(component["height"]) for component in _components(grid)]
    return (
        _lawful(grid)
        and len(set(heights)) > 1
        and _rival_bottom_align(grid) != rule_mirror(grid)
    )


def _gap_witness(grid: list[list[int]]) -> bool:
    return _lawful(grid) and _rival_no_gap(grid) != rule_mirror(grid)


SEMANTIC_RIVALS = {
    "left_to_right_order": _rival_left_to_right,
    "color_only_order": _rival_color_only,
    "width_only_stable_ties": _rival_width_only,
    "width_then_color_skips_height": _rival_width_then_color,
    "width_height_color_final_key": _rival_width_height_color,
    "width_height_shape_ignores_color": _rival_width_height_shape_only,
    "width_height_first_cell_then_color": _rival_width_height_first_cell_then_color,
    "width_height_first_two_cells_then_color": _rival_width_height_first_two_cells_then_color,
    "bottom_align_crops": _rival_bottom_align,
    "pack_without_gap": _rival_no_gap,
}

SEMANTIC_WITNESSES = {
    "width_primary_signal": _width_primary_witness,
    "height_tie_break_signal": _height_tie_witness,
    "lex_shape_signal": _lex_shape_witness,
    "lex_color_signal": _lex_color_witness,
    "input_order_refuted": _left_to_right_witness,
    "top_alignment_required": _top_alignment_witness,
    "one_column_gap_required": _gap_witness,
}

WITNESS_RIVALS = {
    "width_primary_signal": ["color_only_order"],
    "height_tie_break_signal": ["width_then_color_skips_height"],
    "lex_shape_signal": [
        "width_height_color_final_key",
        "width_height_first_cell_then_color",
        "width_height_first_two_cells_then_color",
    ],
    "lex_color_signal": ["width_height_shape_ignores_color"],
    "input_order_refuted": ["left_to_right_order"],
    "top_alignment_required": ["bottom_align_crops"],
    "one_column_gap_required": ["pack_without_gap"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# The official pairs admit a color-only final key and bounded one- and
# two-cell-prefix approximations to the full crop lexicographic key.  Generated
# lex-shape rows must refute all three shortcuts.
CANONICAL_SHORTCUTS = {
    "width_height_color_final_key": _rival_width_height_color,
    "width_height_first_cell_then_color": _rival_width_height_first_cell_then_color,
    "width_height_first_two_cells_then_color": _rival_width_height_first_two_cells_then_color,
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the deterministic six-slot curriculum schedule to the gate."""
    del seed, difficulty
    index = int(sample_index) % len(_SCHEDULE)
    return f"slot{index}:{_SCHEDULE[index]}"


def strict_canonical_like(grid: list[list[int]]) -> list[str]:
    """Task-linked lawful manifold anchored to official canvas/palette scale."""
    errors = self_check(grid)
    if errors:
        return errors
    if f"{len(grid)}x{len(grid[0])}" not in CANVAS_PROFILES:
        return ["canvas is outside the canonical dimension set"]
    palette = {value for row in grid for value in row}
    if len(palette) != 4 or 0 not in palette:
        return ["expected background plus exactly three nonzero colors"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Require the five-demo rotation-robust curriculum to kill named rivals."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]

    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} is missing input/output")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} is outside the task grammar: {errors[0]}")
        elif rule_mirror(demo["input"]) != demo["output"]:
            reasons.append(f"demo {index} disagrees with the canonical rule")

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query is outside the task grammar: {query_errors[0]}")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query disagrees with the canonical rule")

    required = {
        "width-primary": _width_primary_witness,
        "height-tie": _height_tie_witness,
        "lex-shape": _lex_shape_witness,
        "lex-color": _lex_color_witness,
    }
    for name, witness in required.items():
        if not any(witness(demo["input"]) for demo in demos if isinstance(demo, dict)):
            reasons.append(f"demonstrations lack a {name} discriminator")

    for name, competitor in LESSON_COMPETITORS.items():
        valid_demos = [
            demo
            for demo in demos
            if isinstance(demo, dict) and "input" in demo and "output" in demo
        ]
        survives = bool(valid_demos) and all(
            competitor(demo["input"]) == demo["output"] for demo in valid_demos
        )
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} fits every demo but changes the query answer"
            )
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    canvas = ctx.draw_choice("canvas", CANVAS_PROFILES)
    scheduled = _SCHEDULE[int(sample_index) % len(_SCHEDULE)]
    lesson_profile = ctx.draw_choice(
        "lesson_profile",
        LESSON_PROFILES
        if overrides.get("lesson_profile") is not None
        else (scheduled,),
    )
    h, w = (int(value) for value in canvas.split("x"))

    shapes = _select_shapes(
        lesson_profile,
        ctx.draw_rng("shapes"),
        difficulty if isinstance(difficulty, str) else None,
    )
    items = _assign_colors(lesson_profile, shapes, ctx.draw_rng("colors"))
    grid = full_grid(h, w, 0)
    _paint_layout(grid, items, lesson_profile, ctx.draw_rng("layout"))

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError("generated invalid width-gallery scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    requested = {"canvas": canvas, "lesson_profile": lesson_profile}
    if observed != requested:
        raise ValueError(
            f"axis realization mismatch: requested={requested}, observed={observed}"
        )
    if len(rule_mirror(grid)) > 30 or len(rule_mirror(grid)[0]) > 30:
        raise ValueError("generated scene would create an out-of-bounds ARC output")
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-valid three-object input grammar structurally."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and nonempty"]

    errors: list[str] = []
    if len(grid) > 30 or width > 30:
        errors.append(f"grid exceeds ARC limits: {len(grid)}x{width}")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-integer or color outside 0..9")
        return errors
    if not any(value == 0 for row in grid for value in row):
        errors.append("background color 0 is absent")

    components = _components(grid)
    if len(components) != 3:
        errors.append(f"expected exactly three objects, found {len(components)}")
    colors = [int(component["color"]) for component in components]
    if len(colors) != len(set(colors)):
        errors.append("the three objects must use distinct colors")

    if components:
        packed_width = sum(int(component["width"]) for component in components) + max(
            0, len(components) - 1
        )
        packed_height = max(int(component["height"]) for component in components)
        if packed_height > 30 or packed_width > 30:
            errors.append(
                f"packed output would exceed ARC limits: {packed_height}x{packed_width}"
            )
    return errors
